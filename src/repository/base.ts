/** Abstract repository interfaces. */

import type { QuestionSet, AgentResponse } from "../models";

export interface QuestionSetRepository {
  getActive(): Promise<QuestionSet | null>;
  getById(id: string): Promise<QuestionSet | null>;
  create(questionSet: QuestionSet): Promise<void>;
  setActive(id: string): Promise<void>;
  getAll(): Promise<QuestionSet[]>;
}

export interface ResponseRepository {
  save(response: AgentResponse): Promise<void>;
  getByEmail(email: string): Promise<AgentResponse[]>;
  hasResponded(email: string, questionSetId: string): Promise<boolean>;
}
