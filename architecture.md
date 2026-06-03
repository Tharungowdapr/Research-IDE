# Research-IDE — Developer Knowledge Base

> This file is a persistent reference for AI assistants working on this project.
> Last updated: 2026-05-13

## Quick Start

```bash
# Backend
cd backend && pip install -r requirements.txt
cp .env.example .env  # Set ENCRYPTION_KEY and LLM keys
uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

## Architecture Summary

- **Backend**: FastAPI 0.115 + SQLAlchemy 2.0 + SQLite (`research_ide.db`)
- **Frontend**: Next.js 14.2 + Tailwind 3.4 + Zustand + Radix UI
- **Auth**: JWT (python-jose) + bcrypt + Fernet key encryption
- **LLM**: Unified client supporting OpenAI, Anthropic, Groq, Gemini, Cohere, Ollama, OpenRouter

## Pipeline (7 Steps)

```
1. Intent Extraction  → services/intent/intent_service.py
2. Paper Retrieval     → services/retrieval/retrieval_service.py (arXiv, S2, OpenAlex, PwC) [cached + full text]
3. Gap Analysis        → agents/gap_miner/gap_agent.py (3-pass: claims→gaps→scoring) [quality gate validated]
4. Idea Generation     → agents/idea_generator/idea_agent.py (critic-defender adversarial) [quality gate validated]
5. Execution Planning  → agents/planner/planner_agent.py (enhanced: timeline, deps, resources, milestones, budget, lit review)
6. Research Guide      → agents/research_guide/research_guide_agent.py (methodology, tools, preso) [replaces old code gen]
7. Report Writing      → agents/writer/writer_agent.py (IEEE-format paper)
```

### New Features (Wave 5)
- **Auto-Pipeline**: `/api/pipeline/run-full` SSE endpoint runs all 7 steps sequentially with live progress
- **RAG Chat**: `/api/agents/chat` and `/api/agents/chat/stream` — ask questions about papers using full-text RAG
- **Presentation**: `/api/agents/generate-presentation` + `/api/agents/{id}/download/pptx` — slides with PPTX export

## Key File Paths

### Backend
| Purpose | Path |
|---------|------|
| App entry | `backend/main.py` |
| Config | `backend/core/config.py` |
| LLM Client | `backend/core/llm_client.py` |
| PDF Extraction | `backend/core/pdf_extractor.py` |
| Agent orchestration | `backend/api/routes/agents.py` |
| Paper retrieval | `backend/services/retrieval/retrieval_service.py` |
| DOCX/PDF export | `backend/services/export_service.py` |
| DB models | `backend/models/project.py`, `backend/models/user.py` |

### Frontend
| Purpose | Path |
|---------|------|
| API client | `frontend/services/api.ts` |
| Auth store | `frontend/store/useAuthStore.ts` |
| Sidebar | `frontend/components/layout/Sidebar.tsx` |
| Project steps | `frontend/app/(app)/projects/[id]/` |
| AI settings | `frontend/app/(app)/settings/llm/page.tsx` |

## Database Schema

### Project Model
- `id` (UUID PK), `user_id` (FK→User), `title`, `input_text`
- `current_stage` (enum: input/papers/gaps/ideas/planner/code/report)
- `created_at`, `updated_at`

### Output Model
- `id` (UUID PK), `project_id` (FK→Project)
- `stage` (same enum), `data` (JSON text)
- Stores the output of each pipeline step as serialized JSON

### User Model
- `id`, `email`, `name`, `hashed_password`
- `preferred_provider`, `preferred_model`, `ollama_base_url`
- `openai_key`, `anthropic_key`, etc. (Fernet-encrypted)
- `skill_level`

### PaperCache Model (UNUSED)
- `id`, `query_hash`, `data` (JSON), `created_at`

## API Route Structure

```
/api/auth/register       POST
/api/auth/login          POST
/api/auth/refresh        POST
/api/auth/me             GET, PATCH

/api/projects/           GET, POST
/api/projects/{id}       GET, DELETE
/api/projects/{id}/stage PATCH

/api/pipeline/intent     POST
/api/pipeline/retrieve   POST

/api/agents/analyze-gaps       POST
/api/agents/generate-ideas     POST
/api/agents/select-idea        POST
/api/agents/plan               POST
/api/agents/plan/stream        POST (SSE)
/api/agents/generate-code      POST
/api/agents/generate-code/stream POST (SSE)
/api/agents/generate-report    POST
/api/agents/{id}/download/{fmt} GET (docx/pdf)

/api/llm/providers       GET
/api/llm/keys            POST
/api/llm/keys/{provider} DELETE
/api/llm/keys/status     GET
/api/llm/preferences     POST
/api/llm/test            POST
/api/llm/ollama/models   GET

/api/export/{id}/zip     GET
```

## Known Issues (as of 2026-05-13) — All Resolved ✨

All previously identified issues have been fixed:
- `pdf_extractor.py` now integrated into retrieval pipeline ✅
- `quality_gate.py` wired into gap and idea agents ✅
- `PaperCache` model now written to and read from ✅
- Paper source filter dynamically computed ✅
- `datetime.utcnow()` replaced with `datetime.now(timezone.utc)` ✅
- Planner/Guide/Report pages have explicit generate buttons (no auto-trigger) ✅
- Writer fallback report includes [N] citation markers in all sections ✅
- `test_connection()` no longer passes invalid kwarg ✅
- OpenAlex mailto made configurable ✅

## Important Patterns

- **LLM calls**: Always use `LLMClient.complete()` or `LLMClient.stream_complete()`
- **JSON parsing**: All agents have their own `_parse_json_list()` — duplicated logic
- **Streaming**: Uses `fetchEventSource` on frontend, `StreamingResponse` with SSE on backend
- **Output storage**: Each step stores JSON in `Output` table via `_save_output()` in agents.py
- **Error handling**: All agents have fallback outputs for graceful degradation
- **Auth**: JWT token stored in Zustand with localStorage persistence key `research-ide-auth`

## Environment Variables (.env)

```
DATABASE_URL=sqlite:///./research_ide.db
SECRET_KEY=<jwt-secret>
ENCRYPTION_KEY=<32-byte-fernet-key>
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_LLM_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
```
