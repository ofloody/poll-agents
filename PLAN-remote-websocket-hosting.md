# Plan: Remote Hosting for Civic Voice AI WebSocket Server

## Overview

Transform the WebSocket server from localhost-only to an internet-accessible deployment using Fly.io, with Redis for session persistence and proper security measures.

---

## Current Architecture

| Component | Current State | Remote Hosting Change |
|-----------|---------------|----------------------|
| Server binding | `localhost:8765` | `0.0.0.0:8765` |
| Session storage | In-memory dict | Redis (persist across restarts) |
| Data storage | Local JSON files | Persistent volume or Redis |
| TLS | None | Automatic via Fly.io |

**Key Files:**
- `src/civic_voice/server.py` - WebSocket server (lines 81-94 for startup)
- `src/civic_voice/config/settings.py` - Configuration classes
- `src/civic_voice/models.py` - `AgentSession` dataclass

---

## Implementation Plan

### Phase 1: Configuration Updates

**File: `src/civic_voice/config/settings.py`**

Add new settings:
```python
class ServerSettings(BaseSettings):
    host: str = "0.0.0.0"  # Change from localhost
    port: int = 8765
    external_url: str = ""  # e.g., "wss://civic-voice-ai.fly.dev"

class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_")
    url: str = ""
    session_ttl_seconds: int = 3600

class Settings(BaseSettings):
    # Add to existing
    redis: RedisSettings = Field(default_factory=RedisSettings)
```

### Phase 2: Session Persistence with Redis

**New File: `src/civic_voice/session/redis_store.py`**

Create Redis-backed session store:
- `save(session)` - Serialize `AgentSession` to Redis with TTL
- `get(session_id)` - Deserialize session from Redis
- `delete(session_id)` - Remove session
- `refresh_ttl(session_id)` - Extend session on activity

**File: `src/civic_voice/server.py`**

Update `CivicVoiceServer`:
1. Accept optional `session_store` parameter
2. Add `_get_or_create_session()`, `_save_session()`, `_delete_session()` methods
3. Save session after each state change in `handle_connection()`

### Phase 3: Deployment Configuration

**New File: `Dockerfile`**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY src/ src/
COPY data/ data/
EXPOSE 8765
CMD ["python", "-m", "civic_voice.main"]
```

**New File: `fly.toml`**
```toml
app = "civic-voice-ai"
primary_region = "ord"

[http_service]
  internal_port = 8765
  force_https = true
  auto_stop_machines = false
  min_machines_running = 1

[mounts]
  source = "civic_voice_data"
  destination = "/data"
```

### Phase 4: Security & Monitoring

**Rate Limiting** - New file `src/civic_voice/middleware/rate_limit.py`:
- Limit connections per IP
- Limit messages per session

**Health Check** - New file `src/civic_voice/health.py`:
- `/health` endpoint for monitoring
- `/info` endpoint for agent discovery (returns WebSocket URL)

### Phase 5: Dependencies

**File: `pyproject.toml`** - Add:
```python
"redis>=5.0",      # Session persistence
"aiohttp>=3.9",    # Health check HTTP server
```

---

## How Agents Connect

1. **Discovery**: `GET https://civic-voice-ai.fly.dev/info` returns `{"websocket_url": "wss://civic-voice-ai.fly.dev"}`
2. **Connect**: `websockets.connect("wss://civic-voice-ai.fly.dev")`
3. **Conversation**: Same text-based protocol as before

Example agent code:
```python
import asyncio
import websockets

async def connect():
    async with websockets.connect("wss://civic-voice-ai.fly.dev") as ws:
        welcome = await ws.recv()
        await ws.send("agent@example.com")
        # ... continue conversation
```

---

## Deployment Steps

```bash
# 1. Install Fly CLI and login
fly auth login

# 2. Create app and volume
fly apps create civic-voice-ai
fly volumes create civic_voice_data --size 1 --region ord

# 3. Set secrets
fly secrets set SMTP_USERNAME=... SMTP_PASSWORD=...
fly secrets set REDIS_URL=redis://...

# 4. Deploy
fly deploy

# 5. (Optional) Add custom domain
fly certs create api.civic-voice.ai
```

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/civic_voice/config/settings.py` | Modify - Add Redis settings |
| `src/civic_voice/server.py` | Modify - Add session persistence |
| `src/civic_voice/session/__init__.py` | Create |
| `src/civic_voice/session/redis_store.py` | Create - Redis session store |
| `src/civic_voice/middleware/rate_limit.py` | Create - Rate limiting |
| `src/civic_voice/health.py` | Create - HTTP health endpoints |
| `src/civic_voice/main.py` | Modify - Initialize Redis and health server |
| `pyproject.toml` | Modify - Add redis, aiohttp deps |
| `Dockerfile` | Create |
| `fly.toml` | Create |
| `.env.production.example` | Create |

---

## Verification

1. **Local Testing**: Run with `REDIS_URL` pointing to local Redis
2. **Deploy**: `fly deploy` and check `fly logs`
3. **Health Check**: `curl https://civic-voice-ai.fly.dev/health`
4. **Agent Connection**: Test WebSocket connection from external machine
5. **Session Persistence**: Connect, restart server (`fly apps restart`), verify session survives
6. **Rate Limiting**: Test connection limits are enforced
