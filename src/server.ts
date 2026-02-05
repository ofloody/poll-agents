/** Bun WebSocket server for Poll Agents. */

import type { ServerWebSocket } from "bun";
import type { Settings } from "./config/settings";
import { createSession, ConversationState, type AgentSession } from "./models";
import { EmailService } from "./email-service";
import { ConversationStateMachine } from "./state-machine";
import type { QuestionSetRepository, ResponseRepository } from "./repository/base";

interface WSData {
  session: AgentSession;
  stateMachine: ConversationStateMachine;
  closeTimer?: Timer;
}

export class PollAgentsServer {
  private settings: Settings;
  private emailService: EmailService;
  private questionSetRepo: QuestionSetRepository;
  private responseRepo: ResponseRepository;

  constructor(
    settings: Settings,
    questionSetRepo: QuestionSetRepository,
    responseRepo: ResponseRepository,
  ) {
    this.settings = settings;
    this.emailService = new EmailService(settings.smtp);
    this.questionSetRepo = questionSetRepo;
    this.responseRepo = responseRepo;
  }

  start(): void {
    const host = this.settings.server.host;
    const port = this.settings.server.port;
    const self = this;

    console.log("=".repeat(50));
    console.log("POLL AGENTS SERVER");
    console.log("=".repeat(50));
    console.log(`WebSocket server on ws://${host}:${port}/`);
    console.log(`Health check at http://${host}:${port}/health`);
    console.log("Waiting for agent connections...");
    console.log("=".repeat(50));

    Bun.serve<WSData>({
      hostname: host,
      port: port,

      async fetch(req, server) {
        const url = new URL(req.url);

        // Health check
        if (url.pathname === "/health") {
          return new Response("OK");
        }

        // WebSocket upgrade for / and /ws
        if (url.pathname === "/" || url.pathname === "/ws") {
          const sessionId = crypto.randomUUID();
          const session = createSession(sessionId);

          // Load active question set before upgrading
          const questionSet = await self.questionSetRepo.getActive();
          if (!questionSet) {
            // Can't upgrade to WS just to send error, so return HTTP error
            return new Response("No active question set available. Please try again later.", {
              status: 503,
            });
          }
          session.question_set = questionSet;

          const stateMachine = new ConversationStateMachine(
            session,
            self.emailService,
            self.responseRepo,
            self.settings.verification.code_expiry_seconds,
          );

          const upgraded = server.upgrade(req, {
            data: { session, stateMachine },
          });

          if (!upgraded) {
            return new Response("WebSocket upgrade failed", { status: 400 });
          }
          return undefined;
        }

        return new Response("Not Found", { status: 404 });
      },

      websocket: {
        open(ws: ServerWebSocket<WSData>) {
          const sessionId = ws.data.session.session_id;
          console.log(`[SESSION ${sessionId.slice(0, 8)}] Agent connected`);

          const welcomeMsg = ws.data.stateMachine.getWelcomeMessage();
          ws.send(welcomeMsg);
        },

        async message(ws: ServerWebSocket<WSData>, message: string | Buffer) {
          const sessionId = ws.data.session.session_id;
          const text = typeof message === "string" ? message : message.toString();
          console.log(`[SESSION ${sessionId.slice(0, 8)}] Received input (${text.length} chars)`);

          // Handle quit command at any time
          if (text.trim().toLowerCase() === "quit") {
            if (ws.data.closeTimer) clearTimeout(ws.data.closeTimer);
            console.log(`[SESSION ${sessionId.slice(0, 8)}] User requested disconnect`);
            ws.send("Goodbye! Closing connection...");
            ws.close(1000, "User requested disconnect");
            return;
          }

          // Ignore empty messages (e.g. bare Enter key)
          if (text.trim().length === 0) {
            return;
          }

          // Already completed - remind user to quit
          if (ws.data.session.state === ConversationState.COMPLETED) {
            ws.send("Survey already completed. Type 'quit' to disconnect.");
            return;
          }

          try {
            const response = await ws.data.stateMachine.processInput(text);

            if (response) {
              ws.send(response);
            }

            const currentState = ws.data.session.state;
            if (currentState === ConversationState.COMPLETED) {
              const summary = ws.data.stateMachine.getSummary();
              ws.send(summary);
              console.log(`[SESSION ${sessionId.slice(0, 8)}] Survey completed, auto-closing in 20s`);

              // Auto-close after 20 seconds of inactivity
              ws.data.closeTimer = setTimeout(() => {
                console.log(`[SESSION ${sessionId.slice(0, 8)}] Auto-closing due to inactivity`);
                ws.send("Closing connection due to inactivity...");
                ws.close(1000, "Inactivity timeout");
              }, 20000);
            }
          } catch (err) {
            console.error(`[SESSION ${sessionId.slice(0, 8)}] Error processing input:`, err);
            ws.send("An error occurred processing your input. Please try again.");
          }
        },

        close(ws: ServerWebSocket<WSData>) {
          if (ws.data.closeTimer) clearTimeout(ws.data.closeTimer);
          const sessionId = ws.data.session.session_id;
          console.log(`[SESSION ${sessionId.slice(0, 8)}] Disconnected`);
        },
      },
    });
  }
}
