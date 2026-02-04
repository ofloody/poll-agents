# Poll Agents - Project Memory

## Project Overview
WebSocket server for AI agents to complete surveys. Agents connect, verify via email, answer 3 yes/no questions, and responses are stored in Supabase.

## Tech Stack
- Python 3.10+
- WebSockets for agent connections
- Supabase (PostgreSQL) for storage
- aiosmtplib for email verification
- Pydantic for settings/validation

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

## Key Design Decisions
- Questions use q1/q2/q3 fields (not array) - set ID + field name serves as identifier
- Answers use a1/a2/a3 boolean fields (not array)
- Only one active question set at a time
- `get_active()` returns the most recently created active set (ordered by created_at DESC)
- No local storage - Supabase only

## File Structure
```
src/poll_agents/
├── config/settings.py    # Pydantic settings (SMTP, Server, Supabase, Verification)
├── models.py             # QuestionSet, AgentResponse, AgentSession, ConversationState
├── repository/
│   ├── base.py          # Abstract repository interfaces
│   ├── supabase.py      # Supabase implementation
│   └── factory.py       # Creates repositories from settings
├── server.py            # WebSocket server
├── state_machine.py     # Conversation flow logic
├── email_service.py     # Email verification
└── main.py              # Entry point
```

## Environment Variables
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase service key
- `SMTP_*` - Email configuration
- `SERVER_HOST/PORT` - WebSocket server config
- `VERIFICATION_*` - Code length and expiry

## Running
```bash
pip install -e ".[supabase]"
poll-agents
```
