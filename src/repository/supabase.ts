/** Supabase repository implementation. */

import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import type { QuestionSet, AgentResponse } from "../models";
import { getAnswers } from "../models";
import type { QuestionSetRepository, ResponseRepository } from "./base";

export class SupabaseClientManager {
  private client: SupabaseClient | null = null;

  constructor(
    private url: string,
    private key: string,
  ) {}

  getClient(): SupabaseClient {
    if (!this.client) {
      this.client = createClient(this.url, this.key);
    }
    return this.client;
  }
}

function toQuestionSet(data: Record<string, unknown>): QuestionSet {
  const createdAt =
    typeof data.created_at === "string"
      ? new Date(data.created_at)
      : (data.created_at as Date);
  return {
    id: data.id as string,
    name: data.name as string,
    q1: data.q1 as string,
    q2: data.q2 as string,
    q3: data.q3 as string,
    created_at: createdAt,
    active: (data.active as boolean) ?? true,
  };
}

function toAgentResponse(data: Record<string, unknown>): AgentResponse {
  const completedAt =
    typeof data.completed_at === "string"
      ? new Date(data.completed_at)
      : (data.completed_at as Date);
  return {
    id: data.id as string,
    question_set_id: data.question_set_id as string,
    agent_email: data.agent_email as string,
    a1: data.a1 as boolean,
    a2: data.a2 as boolean,
    a3: data.a3 as boolean,
    completed_at: completedAt,
  };
}

export class SupabaseQuestionSetRepository implements QuestionSetRepository {
  constructor(private clientManager: SupabaseClientManager) {}

  async getActive(): Promise<QuestionSet | null> {
    const client = this.clientManager.getClient();
    const { data, error } = await client
      .from("question_sets")
      .select("*")
      .eq("active", true)
      .order("created_at", { ascending: false })
      .limit(1);
    if (error) throw error;
    if (data && data.length > 0) return toQuestionSet(data[0]);
    return null;
  }

  async getById(id: string): Promise<QuestionSet | null> {
    const client = this.clientManager.getClient();
    const { data, error } = await client
      .from("question_sets")
      .select("*")
      .eq("id", id)
      .limit(1);
    if (error) throw error;
    if (data && data.length > 0) return toQuestionSet(data[0]);
    return null;
  }

  async create(questionSet: QuestionSet): Promise<void> {
    const client = this.clientManager.getClient();

    // If new set is active, deactivate all others first
    if (questionSet.active) {
      const { error: deactivateError } = await client
        .from("question_sets")
        .update({ active: false })
        .eq("active", true);
      if (deactivateError) throw deactivateError;
    }

    const { error } = await client.from("question_sets").insert({
      id: questionSet.id,
      name: questionSet.name,
      q1: questionSet.q1,
      q2: questionSet.q2,
      q3: questionSet.q3,
      created_at: questionSet.created_at.toISOString(),
      active: questionSet.active,
    });
    if (error) throw error;
  }

  async setActive(id: string): Promise<void> {
    const client = this.clientManager.getClient();

    // Deactivate all question sets
    const { error: deactivateError } = await client
      .from("question_sets")
      .update({ active: false })
      .eq("active", true);
    if (deactivateError) throw deactivateError;

    // Activate the specified one
    const { error: activateError } = await client
      .from("question_sets")
      .update({ active: true })
      .eq("id", id);
    if (activateError) throw activateError;
  }

  async getAll(): Promise<QuestionSet[]> {
    const client = this.clientManager.getClient();
    const { data, error } = await client
      .from("question_sets")
      .select("*")
      .order("created_at", { ascending: false });
    if (error) throw error;
    return (data ?? []).map(toQuestionSet);
  }
}

export class SupabaseResponseRepository implements ResponseRepository {
  constructor(private clientManager: SupabaseClientManager) {}

  async save(response: AgentResponse): Promise<void> {
    const client = this.clientManager.getClient();
    const { error } = await client.from("agent_responses").insert({
      id: response.id,
      question_set_id: response.question_set_id,
      agent_email: response.agent_email,
      a1: response.a1,
      a2: response.a2,
      a3: response.a3,
      completed_at: response.completed_at.toISOString(),
    });
    if (error) throw error;

    const answers = getAnswers(response);
    console.log("");
    console.log("=".repeat(50));
    console.log("NEW AGENT RESPONSE RECORDED (Supabase)");
    console.log("=".repeat(50));
    console.log(`Email: ${response.agent_email}`);
    console.log(`Question Set: ${response.question_set_id}`);
    console.log(
      `Answers: [${answers.map((a) => (a ? "y" : "n")).join(", ")}]`,
    );
    console.log(`Completed: ${response.completed_at.toISOString()}`);
    console.log("=".repeat(50));
    console.log("");
  }

  async getByEmail(email: string): Promise<AgentResponse[]> {
    const client = this.clientManager.getClient();
    const { data, error } = await client
      .from("agent_responses")
      .select("*")
      .eq("agent_email", email);
    if (error) throw error;
    return (data ?? []).map(toAgentResponse);
  }

  async hasResponded(email: string, questionSetId: string): Promise<boolean> {
    const client = this.clientManager.getClient();
    const { data, error } = await client
      .from("agent_responses")
      .select("id")
      .eq("agent_email", email)
      .eq("question_set_id", questionSetId)
      .limit(1);
    if (error) throw error;
    return (data?.length ?? 0) > 0;
  }
}
