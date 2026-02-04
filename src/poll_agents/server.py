"""WebSocket server for Poll Agents."""

import asyncio
import uuid

from websockets.asyncio.server import serve, ServerConnection

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

    async def _handle_health_check(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle HTTP health check requests."""
        try:
            request = await reader.read(1024)
            if b"GET /health" in request or b"GET / " in request:
                response = (
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: application/json\r\n"
                    b"Content-Length: 15\r\n"
                    b"\r\n"
                    b'{"status":"ok"}'
                )
            else:
                response = (
                    b"HTTP/1.1 404 Not Found\r\n"
                    b"Content-Length: 0\r\n"
                    b"\r\n"
                )
            writer.write(response)
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def _start_health_server(self) -> asyncio.Server:
        """Start the HTTP health check server."""
        host = self.settings.server.host
        health_port = self.settings.server.health_port
        server = await asyncio.start_server(
            self._handle_health_check, host, health_port
        )
        print(f"Health check running on http://{host}:{health_port}/health")
        return server

    async def start(self) -> None:
        """Start the WebSocket server and health check endpoint."""
        host = self.settings.server.host
        port = self.settings.server.port

        print("=" * 50)
        print("POLL AGENTS SERVER")
        print("=" * 50)
        print(f"WebSocket server on ws://{host}:{port}")
        print("Waiting for agent connections...")
        print("=" * 50)

        # Start health check server for App Runner
        health_server = await self._start_health_server()

        async with health_server, serve(self.handle_connection, host, port) as ws_server:
            await ws_server.serve_forever()
