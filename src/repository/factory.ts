/** Repository factory. */

import type { Settings } from "../config/settings";
import { isSupabaseConfigured } from "../config/settings";
import type { QuestionSetRepository, ResponseRepository } from "./base";
import {
  SupabaseClientManager,
  SupabaseQuestionSetRepository,
  SupabaseResponseRepository,
} from "./supabase";

export function createRepositories(settings: Settings): [QuestionSetRepository, ResponseRepository] {
  if (!isSupabaseConfigured(settings.supabase)) {
    throw new Error("SUPABASE_URL and SUPABASE_KEY must be set in environment");
  }

  const clientManager = new SupabaseClientManager(
    settings.supabase.url,
    settings.supabase.key,
  );

  return [
    new SupabaseQuestionSetRepository(clientManager),
    new SupabaseResponseRepository(clientManager),
  ];
}
