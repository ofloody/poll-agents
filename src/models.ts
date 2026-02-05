/** Domain models for Poll Agents. */

export enum ConversationState {
  WELCOME = "WELCOME",
  AWAITING_EMAIL = "AWAITING_EMAIL",
  AWAITING_VERIFICATION = "AWAITING_VERIFICATION",
  ASKING_QUESTION_1 = "ASKING_QUESTION_1",
  ASKING_QUESTION_2 = "ASKING_QUESTION_2",
  ASKING_QUESTION_3 = "ASKING_QUESTION_3",
  COMPLETED = "COMPLETED",
  DISCONNECTED = "DISCONNECTED",
}

export interface QuestionSet {
  id: string;
  name: string;
  q1: string;
  q2: string;
  q3: string;
  created_at: Date;
  active: boolean;
}

export function getQuestions(qs: QuestionSet): [string, string, string] {
  return [qs.q1, qs.q2, qs.q3];
}

export interface AgentResponse {
  id: string;
  question_set_id: string;
  agent_email: string;
  a1: boolean;
  a2: boolean;
  a3: boolean;
  completed_at: Date;
}

export function getAnswers(ar: AgentResponse): [boolean, boolean, boolean] {
  return [ar.a1, ar.a2, ar.a3];
}

export interface AgentSession {
  session_id: string;
  state: ConversationState;
  email: string | null;
  verification_code: string | null;
  verification_code_created: Date | null;
  verification_attempts: number;
  question_set: QuestionSet | null;
  answers: Map<number, boolean>;
  created_at: Date;
}

export function createSession(sessionId: string): AgentSession {
  return {
    session_id: sessionId,
    state: ConversationState.WELCOME,
    email: null,
    verification_code: null,
    verification_code_created: null,
    verification_attempts: 0,
    question_set: null,
    answers: new Map(),
    created_at: new Date(),
  };
}
