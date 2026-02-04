# Plan: Supabase Database Integration

## Overview

Add Supabase as a persistent storage backend, replacing local JSON files with a remote PostgreSQL database. The existing repository pattern makes this a clean swap.

---

## Database Schema (Supabase SQL)

```sql
-- Question Sets table
CREATE TABLE question_sets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    questions JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT questions_array_length CHECK (jsonb_array_length(questions) = 3)
);

-- Agent Responses table
CREATE TABLE agent_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_set_id UUID NOT NULL REFERENCES question_sets(id),
    agent_email VARCHAR(255) NOT NULL,
    answers JSONB NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT answers_array_length CHECK (jsonb_array_length(answers) = 3)
);

-- Indexes
CREATE INDEX idx_question_sets_active ON question_sets(active) WHERE active = TRUE;
CREATE INDEX idx_agent_responses_email ON agent_responses(agent_email);

-- Ensure only one active question set
CREATE UNIQUE INDEX idx_single_active_question_set ON question_sets(active) WHERE active = TRUE;
```

---

## Implementation Plan

### Phase 1: Configuration

**File: `src/civic_voice/config/settings.py`**

Add Supabase settings:
```python
class SupabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SUPABASE_")
    url: str = ""
    key: str = ""  # Service role key

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.key)

class Settings(BaseSettings):
    # Add to existing fields
    supabase: SupabaseSettings = Field(default_factory=SupabaseSettings)
```

### Phase 2: Supabase Repository

**New File: `src/civic_voice/repository/supabase.py`**

```python
class SupabaseClientManager:
    """Manages async Supabase client lifecycle."""
    async def get_client(self) -> AsyncClient
    async def close() -> None

class SupabaseQuestionSetRepository(QuestionSetRepository):
    async def get_active(self) -> Optional[QuestionSet]
    async def get_by_id(self, id: str) -> Optional[QuestionSet]
    async def create(self, question_set: QuestionSet) -> None

class SupabaseResponseRepository(ResponseRepository):
    async def save(self, response: AgentResponse) -> None
    async def get_by_email(self, email: str) -> list[AgentResponse]
```

### Phase 3: Repository Factory

**New File: `src/civic_voice/repository/factory.py`**

```python
def create_repositories(settings: Settings) -> Tuple[QuestionSetRepository, ResponseRepository]:
    backend = settings.storage.backend.lower()

    if backend == "local":
        return (LocalQuestionSetRepository(...), LocalResponseRepository(...))

    elif backend == "supabase":
        client_manager = SupabaseClientManager(settings.supabase.url, settings.supabase.key)
        return (SupabaseQuestionSetRepository(client_manager), SupabaseResponseRepository(client_manager))
```

### Phase 4: Update Entry Point

**File: `src/civic_voice/main.py`**

```python
from .repository.factory import create_repositories

def main():
    settings = Settings()
    question_set_repo, response_repo = create_repositories(settings)
    print(f"Using storage backend: {settings.storage.backend}")
    # ... rest unchanged
```

### Phase 5: Dependencies

**File: `pyproject.toml`**

```toml
[project.optional-dependencies]
supabase = ["supabase>=2.0"]
```

Install with: `pip install -e ".[supabase]"`

---

## Environment Variables

```bash
# .env
STORAGE_BACKEND=supabase

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/civic_voice/config/settings.py` | Modify - Add SupabaseSettings |
| `src/civic_voice/repository/supabase.py` | Create - Supabase implementations |
| `src/civic_voice/repository/factory.py` | Create - Backend switching logic |
| `src/civic_voice/repository/__init__.py` | Modify - Export factory |
| `src/civic_voice/main.py` | Modify - Use factory |
| `pyproject.toml` | Modify - Add supabase optional dep |
| `scripts/migrate_to_supabase.py` | Create - Data migration script |

---

## Migration Script

**New File: `scripts/migrate_to_supabase.py`**

Reads existing `data/question_sets.json` and `data/responses.json`, uploads to Supabase using upsert.

---

## Verification

1. **Schema**: Run SQL in Supabase SQL Editor
2. **Local Test**: `STORAGE_BACKEND=local python -m civic_voice.main` (regression)
3. **Supabase Test**: `STORAGE_BACKEND=supabase python -m civic_voice.main`
4. **Migration**: Run `python scripts/migrate_to_supabase.py`
5. **End-to-End**: Connect agent, complete survey, verify response in Supabase dashboard
