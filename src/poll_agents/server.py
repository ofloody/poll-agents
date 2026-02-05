"""WebSocket server for Poll Agents."""

import asyncio
import uuid

from websockets.asyncio.server import serve, ServerConnection
from websockets.datastructures import Headers
from websockets.http11 import Request, Response

from .config.settings import Settings
from .models import AgentSession, ConversationState
from .email_service import EmailService
from .state_machine import ConversationStateMachine
from .repository.base import QuestionSetRepository, ResponseRepository


class PollAgentsServer:
    """WebSocket server for AI agent survey conversations."""

    def __init__(
        self,
        settings: Settings,
        question_set_repo: QuestionSetRepository,
        response_repo: ResponseRepository,
    ):
        self.settings = settings
        self.email_service = EmailService(settings.smtp)
        self.question_set_repo = question_set_repo
        self.response_repo = response_repo
        self.active_sessions: dict[str, AgentSession] = {}

    async def handle_connection(self, websocket: ServerConnection) -> None:
        """Handle a single WebSocket connection."""
        session_id = str(uuid.uuid4())
        session = AgentSession(session_id=session_id)
        self.active_sessions[session_id] = session

        print(f"[SESSION {session_id[:8]}] Agent connected")

        try:
            # Load active question set
            question_set = await self.question_set_repo.get_active()
            if not question_set:
                await websocket.send("No active question set available. Please try again later.")
                return

            session.question_set = question_set

            # Initialize state machine
            state_machine = ConversationStateMachine(
                session=session,
                email_service=self.email_service,
                response_repository=self.response_repo,
                code_expiry_seconds=self.settings.verification.code_expiry_seconds,
            )

            # Send welcome message
            welcome_msg = state_machine.get_welcome_message()
            await websocket.send(welcome_msg)

            # Main conversation loop
            async for message in websocket:
                # Log message receipt without exposing sensitive content
                print(f"[SESSION {session_id[:8]}] Received input ({len(message)} chars)")

                response = await state_machine.process_input(message)

                if response:
                    await websocket.send(response)

                if session.state == ConversationState.COMPLETED:
                    # Send summary and close
                    summary = state_machine.get_summary()
                    await websocket.send(summary)
                    print(f"[SESSION {session_id[:8]}] Completed - closing connection")
                    await websocket.close(1000, "Survey complete")
                    break

        except Exception as e:
            print(f"[SESSION {session_id[:8]}] Error: {e}")
        finally:
            del self.active_sessions[session_id]
            print(f"[SESSION {session_id[:8]}] Disconnected")

    async def health_check(self, connection, request: Request) -> Response | None:
        """Handle HTTP health check requests."""
        if request.path == "/health":
            return Response(200, "OK", Headers([("Content-Type", "text/plain")]), b"OK")
        return None  # Continue with WebSocket upgrade

    async def start(self) -> None:
        """Start the WebSocket server."""
        host = self.settings.server.host
        port = self.settings.server.port

        print("=" * 50)
        print("POLL AGENTS SERVER")
        print("=" * 50)
        print(f"WebSocket server on wss://{host}:{port}")
        print(f"Health check at http://{host}:{port}/health")
        print("Waiting for agent connections...")
        print("=" * 50)

        async with serve(
            self.handle_connection,
            host,
            port,
            process_request=self.health_check,
        ) as ws_server:
            await ws_server.serve_forever()
