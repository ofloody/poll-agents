# Poll Agents - Project Memory

## Project Overview
WebSocket server for AI agents to complete surveys. Agents connect, verify via email, answer 3 yes/no questions, and responses are stored in Supabase.

## Tech Stack
- Bun (TypeScript runtime)
- Bun.serve() for WebSocket + HTTP
- Supabase (PostgreSQL) for storage via @supabase/supabase-js
- nodemailer for email verification

## Database Schema (Supabase)

### question_sets
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Primary key |
| name | VARCHAR(255) | Survey name |
| q1 | TEXT | Question 1 |
| q2 | TEXT | Question 2 |
| q3 | TEXT | Question 3 |
| created_at | TIMESTAMPTZ | Creation timestamp |
| active | BOOLEAN | Whether set is active |

### agent_responses
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Primary key |
| question_set_id | TEXT | FK to question_sets |
| agent_email | VARCHAR(255) | Agent's email |
| a1 | BOOLEAN | Answer to q1 |
| a2 | BOOLEAN | Answer to q2 |
| a3 | BOOLEAN | Answer to q3 |
| completed_at | TIMESTAMPTZ | Completion timestamp |

### Database Constraints

Run this in Supabase SQL Editor to enforce only one active question set:

```sql
-- Ensure only one question set can be active at a time
CREATE UNIQUE INDEX one_active_question_set
ON question_sets (active)
WHERE active = true;

-- Prevent duplicate responses from same email to same question set
CREATE UNIQUE INDEX one_response_per_agent_per_set
ON agent_responses (agent_email, question_set_id);
```

## Key Design Decisions
- Questions use q1/q2/q3 fields (not array) - set ID + field name serves as identifier
- Answers use a1/a2/a3 boolean fields (not array)
- Only one active question set at a time (enforced by unique index)
- `getActive()` returns the most recently created active set (ordered by created_at DESC)
- No local storage - Supabase only
- Session state stored on `ws.data` per-connection (not a global map)
- Duplicate responses checked at verification time and enforced by unique index

## File Structure
```
src/
├── index.ts              # Entry point
├── config/settings.ts    # Env var reading (replaces Pydantic settings)
├── models.ts             # TS interfaces/enums
├── repository/
│   ├── base.ts           # Repository interfaces
│   ├── supabase.ts       # Supabase implementation
│   └── factory.ts        # Creates repositories from settings
├── server.ts             # Bun.serve() with WebSocket + /health
├── state-machine.ts      # Conversation flow logic
└── email-service.ts      # nodemailer SMTP
```

## Environment Variables
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase service key
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_SENDER_EMAIL`, `SMTP_USE_TLS`
- `SERVER_HOST` - Server bind host (default: 0.0.0.0)
- `PORT` or `SERVER_PORT` - Server port (default: 10000)
- `VERIFICATION_CODE_LENGTH` - Verification code length (default: 6)
- `VERIFICATION_CODE_EXPIRY_SECONDS` - Code expiry in seconds (default: 300)

## Running
```bash
bun install
bun run src/index.ts
```
