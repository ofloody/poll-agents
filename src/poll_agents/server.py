"""WebSocket server for Poll Agents."""

import asyncio
import uuid

from aiohttp import web, WSMsgType

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

    async def health_check(self, request: web.Request) -> web.Response:
        """Handle HTTP health check requests (GET and HEAD)."""
        return web.Response(text="OK")

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        session_id = str(uuid.uuid4())
        session = AgentSession(session_id=session_id)
        self.active_sessions[session_id] = session

        print(f"[SESSION {session_id[:8]}] Agent connected")

        try:
            # Load active question set
            question_set = await self.question_set_repo.get_active()
            if not question_set:
                await ws.send_str("No active question set available. Please try again later.")
                await ws.close()
                return ws

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
            await ws.send_str(welcome_msg)

            # Main conversation loop
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    message = msg.data
                    print(f"[SESSION {session_id[:8]}] Received input ({len(message)} chars)")

                    response = await state_machine.process_input(message)

                    if response:
                        await ws.send_str(response)

                    if session.state == ConversationState.COMPLETED:
                        summary = state_machine.get_summary()
                        await ws.send_str(summary)
                        print(f"[SESSION {session_id[:8]}] Completed - closing connection")
                        await ws.close()
                        break

                elif msg.type == WSMsgType.ERROR:
                    print(f"[SESSION {session_id[:8]}] WebSocket error: {ws.exception()}")

        except Exception as e:
            print(f"[SESSION {session_id[:8]}] Error: {e}")
        finally:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            print(f"[SESSION {session_id[:8]}] Disconnected")

        return ws

    async def start(self) -> None:
        """Start the server."""
        host = self.settings.server.host
        port = self.settings.server.port

        app = web.Application()
        app.router.add_get("/health", self.health_check)
        app.router.add_route("HEAD", "/health", self.health_check)
        app.router.add_get("/", self.websocket_handler)
        app.router.add_get("/ws", self.websocket_handler)

        print("=" * 50)
        print("POLL AGENTS SERVER")
        print("=" * 50)
        print(f"WebSocket server on ws://{host}:{port}/")
        print(f"Health check at http://{host}:{port}/health")
        print("Waiting for agent connections...")
        print("=" * 50)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        # Keep running forever
        while True:
            await asyncio.sleep(3600)
