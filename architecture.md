# Research-IDE — Developer Knowledge Base

> Persistent reference for AI assistants and developers working on this project.
> Last updated: 2026-07-12

## Live Deployment

| Service | URL |
|---------|-----|
| Frontend | https://research-ide-frontend.vercel.app |
| Backend | https://research-ide-backend.onrender.com |
| API Docs | https://research-ide-backend.onrender.com/api/docs |
| Database | Neon PostgreSQL (free tier) |

## Quick Start

```bash
# Backend
cd backend && pip install -r requirements.txt
cp .env.example .env  # Set SECRET_KEY, ENCRYPTION_KEY, and LLM keys
uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

## Architecture Summary

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL (Neon) on Render free tier (512MB RAM)
- **Frontend**: Next.js 14 + Tailwind CSS + Zustand on Vercel
- **Auth**: JWT (python-jose) + bcrypt + Fernet key encryption
- **LLM**: Unified client supporting 7 providers with auto-fallback
- **NLP**: spaCy with pure-Python fallback (no heavy ML dependencies on Render)

## Pipeline (7 Steps)

```
1. Intent Extraction  → services/nlp_analysis/analyzer.py
2. Paper Retrieval     → services/retrieval/retrieval_service.py (arXiv, S2, OpenAlex, PwC) [cached + full text]
3. Gap Analysis        → agents/gap_miner/gap_agent.py (3-pass: claims → gaps → scoring) [quality gate validated]
4. Idea Generation     → agents/idea_generator/idea_agent.py (critic-defender adversarial) [quality gate validated]
5. Execution Planning  → agents/planner/planner_agent.py (2-pass: base + enrichment)
6. Research Guide      → agents/research_guide_agent.py (guide + PPTX slides)
7. Report Writing      → agents/writer/writer_agent.py (IEEE-format paper with citations)
```

### Pipeline SSE Streaming
- `/api/pipeline/run-full` — runs all 7 steps sequentially with live progress
- Plan and Code generation support SSE streaming

## Key File Paths

### Backend
| Purpose | Path |
|---------|------|
| App entry | `backend/main.py` |
| Config | `backend/core/config.py` |
| LLM Client | `backend/core/llm_client.py` |
| NLP Analyzer | `backend/services/nlp_analysis/analyzer.py` |
| PDF Extraction | `backend/core/pdf_extractor.py` |
| Agent orchestration | `backend/api/routes/agents.py` |
| Paper retrieval | `backend/services/retrieval/retrieval_service.py` |
| PDF/DOCX/PPTX export | `backend/services/export_service.py` |
| DB models | `backend/models/project.py`, `backend/models/user.py` |
| Security | `backend/core/security.py` |

### Frontend
| Purpose | Path |
|---------|------|
| API client | `frontend/services/api.ts` |
| Auth store | `frontend/store/useAuthStore.ts` |
| Sidebar | `frontend/components/layout/Sidebar.tsx` |
| Project steps | `frontend/app/(app)/projects/[id]/` |
| LLM settings | `frontend/app/(app)/settings/llm/page.tsx` |
| SSE hook | `frontend/hooks/useStream.ts` |

## Database Schema

### User
- `id` (UUID PK), `email` (unique), `name`, `hashed_password`
- `preferred_provider`, `preferred_model`, `ollama_base_url`
- `llm_api_keys` (JSON — Fernet-encrypted API keys per provider)
- `skill_level`, `interests`

### Project
- `id` (UUID PK), `user_id` (FK → User)
- `title`, `input_text`, `status`, `current_stage`
- `created_at`, `updated_at`

### Output
- `id` (UUID PK), `project_id` (FK → Project)
- `output_type` (string: "intent", "papers", "analysis", "gaps", "ideas", "selected_idea", "objectives", "plan", "data_plan", "code", "experiments", "analysis_template", "guide", "presentation", "report", "review")
- `data` (JSON text)

### PaperCache
- `external_id` (PK), `title`, `abstract`, `full_text`, `authors`, `year`, `citations`, `source`, `url`

### UsageLog
- `id`, `user_id` (FK), `provider`, `model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `cost_usd`, `energy_wh`

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
/api/pipeline/analyze    POST  (NLP analysis — local, no LLM)
/api/pipeline/run-full   POST  (SSE — full 7-step pipeline)

/api/agents/analyze-gaps        POST
/api/agents/generate-ideas      POST
/api/agents/select-idea         POST
/api/agents/plan                POST
/api/agents/plan/stream         POST (SSE)
/api/agents/generate-code       POST
/api/agents/generate-code/stream POST (SSE)
/api/agents/generate-report     POST
/api/agents/{id}/download/docx  GET
/api/agents/{id}/download/pdf   GET
/api/agents/{id}/download/pptx  GET
/api/agents/save-report         POST

/api/llm/providers       GET
/api/llm/keys            POST
/api/llm/keys/{provider} DELETE
/api/llm/keys/status     GET
/api/llm/preferences     POST
/api/llm/test            POST

/api/export/{id}/export/full    GET  (ZIP)

/api/health               GET
```

## Environment Variables

### Backend
```
DATABASE_URL=postgresql://... (Neon) or sqlite:///./research_ide.db (local)
SECRET_KEY=<fixed random string — must persist across deploys>
ENCRYPTION_KEY=<fixed random string — must persist across deploys>
DEFAULT_LLM_PROVIDER=groq
GROQ_API_KEY=<your-key>
ALLOWED_ORIGINS=["http://localhost:3000"]  (local) or ["https://...vercel.app"] (deployed)
```

### Frontend
```
NEXT_PUBLIC_API_URL=http://localhost:8000 (local) or https://...onrender.com (deployed)
```

## Key Design Decisions

- **NLP analysis is pure local** — `analyze_text()` uses regex + TF + heuristics. No spaCy/KeyBERT/sentence-transformers required (saves ~500MB RAM on Render)
- **LLM auto-fallback** — `build_llm_client_for_user()` checks env vars when user has no key; auto-switches from ollama to groq if `GROQ_API_KEY` is set
- **Export fonts are cross-platform** — PDF uses Times New Roman TTFs on Windows, fpdf2 built-in Times on Linux
- **Rate limiter is in-memory** — `_login_attempts` dict with background pruning; not persistent across restarts
- **All agent outputs** go through `_save_output()` which upserts by (project_id, output_type)

## Common Patterns

- **LLM calls**: `LLMClient.complete()` or `LLMClient.stream_complete()`
- **JSON parsing**: `parse_json_response()` in `core/utils.py` with fence-stripping and recovery
- **Streaming**: `fetchEventSource` on frontend, `StreamingResponse` with SSE on backend
- **Auth**: JWT token in Zustand store with localStorage persistence key `research-ide-auth`
- **Error handling**: All agents have `_fallback_*()` functions for graceful degradation
