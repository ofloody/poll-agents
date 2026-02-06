/** Configuration settings from environment variables. */

export interface SMTPSettings {
  host: string;
  port: number;
  username: string;
  password: string;
  sender_email: string;
  use_tls: boolean;
}

export interface ServerSettings {
  host: string;
  port: number;
}

export interface SupabaseSettings {
  url: string;
  key: string;
}

export interface VerificationSettings {
  code_length: number;
  code_expiry_seconds: number;
  pre_auth_code_expiry_seconds: number;
}

export interface Settings {
  smtp: SMTPSettings;
  server: ServerSettings;
  supabase: SupabaseSettings;
  verification: VerificationSettings;
}

function envStr(key: string, fallback: string = ""): string {
  return process.env[key] ?? fallback;
}

function envInt(key: string, fallback: number): number {
  const v = process.env[key];
  if (v === undefined) return fallback;
  const n = parseInt(v, 10);
  return isNaN(n) ? fallback : n;
}

function envBool(key: string, fallback: boolean): boolean {
  const v = process.env[key];
  if (v === undefined) return fallback;
  return v.toLowerCase() === "true" || v === "1";
}

export function loadSettings(): Settings {
  return {
    smtp: {
      host: envStr("SMTP_HOST", "smtp.gmail.com"),
      port: envInt("SMTP_PORT", 587),
      username: envStr("SMTP_USERNAME"),
      password: envStr("SMTP_PASSWORD"),
      sender_email: envStr("SMTP_SENDER_EMAIL"),
      use_tls: envBool("SMTP_USE_TLS", true),
    },
    server: {
      host: envStr("SERVER_HOST", "0.0.0.0"),
      port: envInt("PORT", envInt("SERVER_PORT", 10000)),
    },
    supabase: {
      url: envStr("SUPABASE_URL"),
      key: envStr("SUPABASE_KEY"),
    },
    verification: {
      code_length: envInt("VERIFICATION_CODE_LENGTH", 6),
      code_expiry_seconds: envInt("VERIFICATION_CODE_EXPIRY_SECONDS", 300),
      pre_auth_code_expiry_seconds: envInt("PRE_AUTH_CODE_EXPIRY_SECONDS", 600),
    },
  };
}

export function isSupabaseConfigured(settings: SupabaseSettings): boolean {
  return Boolean(settings.url && settings.key);
}
