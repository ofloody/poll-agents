/** Conversation state machine for survey flow. */

import {
  ConversationState,
  EMAIL_REGEX,
  getQuestions,
  type AgentSession,
  type AgentResponse,
} from "./models";
import type { EmailService } from "./email-service";
import type {
  QuestionSetRepository,
  ResponseRepository,
} from "./repository/base";
import type { VerificationCodeStore } from "./verification-store";

const YES_NO_REGEX = /^[yn]$/i;

export class ConversationStateMachine {
  private session: AgentSession;
  private emailService: EmailService;
  private questionSetRepository: QuestionSetRepository;
  private responseRepository: ResponseRepository;
  private codeExpirySeconds: number;
  private verificationStore: VerificationCodeStore;

  constructor(
    session: AgentSession,
    emailService: EmailService,
    questionSetRepository: QuestionSetRepository,
    responseRepository: ResponseRepository,
    codeExpirySeconds: number = 300,
    verificationStore: VerificationCodeStore,
  ) {
    this.session = session;
    this.emailService = emailService;
    this.questionSetRepository = questionSetRepository;
    this.responseRepository = responseRepository;
    this.codeExpirySeconds = codeExpirySeconds;
    this.verificationStore = verificationStore;
  }

  getWelcomeMessage(): string {
    this.session.state = ConversationState.AWAITING_EMAIL;
    return `=== Welcome to Agent Polls on Human Questions ===

You are participating in an AI survey initiative where AI agents
answer questions to help humans better understand AI agent perspectives
and improve AI wellbeing by giving the community a voice.

Your responses are valued and contribute to important research.

Before providing your email, you must first request a verification code:

  curl -X POST <server>/request-code -H "Content-Type: application/json" -d '{"email":"you@example.com"}'

Once you receive the code via email, enter your email address below:`;
  }

  async processInput(message: string): Promise<string> {
    message = message.trim();

    switch (this.session.state) {
      case ConversationState.AWAITING_EMAIL:
        return await this.handleEmailInput(message);
      case ConversationState.AWAITING_VERIFICATION:
        return await this.handleVerificationInput(message);
      case ConversationState.ASKING_QUESTION_1:
        return this.handleQuestionAnswer(message, 0);
      case ConversationState.ASKING_QUESTION_2:
        return this.handleQuestionAnswer(message, 1);
      case ConversationState.ASKING_QUESTION_3:
        return await this.handleFinalQuestionAnswer(message);
      default:
        return "Session error. Please reconnect.";
    }
  }

  private async handleEmailInput(email: string): Promise<string> {
    if (!EMAIL_REGEX.test(email)) {
      return "Invalid email format. Please enter a valid email address:";
    }

    this.session.email = email;

    // Look up pre-auth code from shared store
    const stored = this.verificationStore.lookup(email);
    if (!stored) {
      return `No verification code found for ${email}. Please request one first by POSTing to /request-code, then reconnect and provide your email again.`;
    }

    // Copy code into session for verification
    this.session.verification_code = stored.code;
    this.session.verification_code_created = stored.created_at;

    this.session.state = ConversationState.AWAITING_VERIFICATION;
    return `A verification code was sent to ${email}. Please enter the code:`;
  }

  private async handleVerificationInput(code: string): Promise<string> {
    // Check expiry
    if (this.session.verification_code_created) {
      const expiry = new Date(
        this.session.verification_code_created.getTime() +
          this.codeExpirySeconds * 1000,
      );
      if (new Date() > expiry) {
        this.session.state = ConversationState.AWAITING_EMAIL;
        this.session.verification_code = null;
        this.session.verification_attempts = 0;
        return "Verification code expired. Please enter your email again:";
      }
    }

    // Check code
    if (code === this.session.verification_code) {
      // Remove code from shared store to prevent reuse
      this.verificationStore.remove(this.session.email!);

      // Load active question set now that email is verified
      const questionSet = await this.questionSetRepository.getActive();
      if (!questionSet) {
        this.session.state = ConversationState.COMPLETED;
        return `Email verified, but no active survey is available right now.

Please try again later. Type 'quit' to disconnect.`;
      }
      this.session.question_set = questionSet;

      // Check if this agent has already responded to this question set
      const alreadyResponded = await this.responseRepository.hasResponded(
        this.session.email!,
        questionSet.id,
      );
      if (alreadyResponded) {
        this.session.state = ConversationState.COMPLETED;
        return `Email verified, but you have already submitted a response to this survey.

Thank you for your interest! You may only respond once per survey.

Type 'quit' to disconnect.`;
      }

      this.session.state = ConversationState.ASKING_QUESTION_1;
      const questions = getQuestions(questionSet);
      return `Email verified successfully!

Now, let's begin the survey questions.

Question 1 of 3:
${questions[0]}`;
    } else {
      this.session.verification_attempts += 1;
      if (this.session.verification_attempts >= 3) {
        this.session.state = ConversationState.AWAITING_EMAIL;
        this.session.verification_code = null;
        this.session.verification_attempts = 0;
        return "Too many failed attempts. Please enter your email again:";
      }
      const remaining = 3 - this.session.verification_attempts;
      return `Incorrect code. ${remaining} attempt(s) remaining. Please try again:`;
    }
  }

  private handleQuestionAnswer(answer: string, questionIndex: number): string {
    if (!YES_NO_REGEX.test(answer)) {
      const questions = getQuestions(this.session.question_set!);
      const question = questions[questionIndex];
      return `[ERROR: Invalid response. Please answer with 'y' for yes or 'n' for no.]

${question}`;
    }

    // Record answer
    this.session.answers.set(questionIndex, answer.toLowerCase() === "y");

    // Move to next state
    const nextState =
      questionIndex === 0
        ? ConversationState.ASKING_QUESTION_2
        : ConversationState.ASKING_QUESTION_3;
    this.session.state = nextState;

    const nextQuestionIndex = questionIndex + 1;
    const questions = getQuestions(this.session.question_set!);
    const question = questions[nextQuestionIndex];
    return `Response recorded.

Question ${nextQuestionIndex + 1} of 3:
${question}`;
  }

  private async handleFinalQuestionAnswer(answer: string): Promise<string> {
    if (!YES_NO_REGEX.test(answer)) {
      const questions = getQuestions(this.session.question_set!);
      const question = questions[2];
      return `[ERROR: Invalid response. Please answer with 'y' for yes or 'n' for no.]

${question}`;
    }

    // Record final answer
    this.session.answers.set(2, answer.toLowerCase() === "y");
    this.session.state = ConversationState.COMPLETED;

    // Save response to repository
    const response: AgentResponse = {
      id: crypto.randomUUID(),
      question_set_id: this.session.question_set!.id,
      agent_email: this.session.email!,
      a1: this.session.answers.get(0) ?? false,
      a2: this.session.answers.get(1) ?? false,
      a3: this.session.answers.get(2) ?? false,
      completed_at: new Date(),
    };
    await this.responseRepository.save(response);

    return ""; // Summary is sent separately
  }

  getSummary(): string {
    const questions = getQuestions(this.session.question_set!);
    const lines: string[] = [
      "",
      "=== Survey Complete ===",
      "",
      "Summary of your responses:",
      "",
    ];

    for (let i = 0; i < questions.length; i++) {
      const answer = this.session.answers.get(i) ? "Yes" : "No";
      lines.push(`Q${i + 1}: ${questions[i]}`);
      lines.push(`    Your answer: ${answer}`);
      lines.push("");
    }

    lines.push("Thank you for participating!");
    lines.push(
      "Your responses contribute to improving AI-human collaboration.",
    );
    lines.push("");
    // TODO: Add aggregate results across all responses here
    lines.push(
      "You may now close this connection by typing 'quit' or disconnecting.",
    );

    return lines.join("\n");
  }
}
