# ResearchIDE

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python) ![Node](https://img.shields.io/badge/Node-18+-green?logo=node.js) ![License](https://img.shields.io/badge/License-MIT-yellow) ![CI](https://github.com/Tharungowdapr/Research-IDE/actions/workflows/ci.yml/badge.svg)

**AI-Powered Research Assistant** — From research question to paper, code, and report in 7 guided steps.

---

## Live Demo

| Service | URL | Notes |
|---------|-----|-------|
| **Frontend** | [research-ide-frontend.vercel.app](https://research-ide-frontend.vercel.app) | Next.js on Vercel |
| **Backend API** | [research-ide-backend.onrender.com](https://research-ide-backend.onrender.com) | FastAPI on Render |
| **API Docs** | [research-ide-backend.onrender.com/api/docs](https://research-ide-backend.onrender.com/api/docs) | Swagger UI |

> **Note:** The backend sleeps after 15 min of inactivity on the free tier. First request may take ~30s to wake up.

---

## Documentation

| Document | Description |
|----------|-------------|
| [architecture.md](architecture.md) | Developer knowledge base: file paths, database schema, API routes |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development workflow, code style, commit conventions |
| [CHANGELOG.md](CHANGELOG.md) | Version history and release notes |
| [viva-qa.md](viva-qa.md) | Viva / evaluation Q&A covering NLP, LLM, retrieval, architecture |

---

## Features

- **NLP Intent Extraction** — Rule-based domain classification, keyphrase extraction, NER (spaCy with pure-Python fallback)
- **Multi-Source Paper Retrieval** — arXiv, Semantic Scholar, OpenAlex, PapersWithCode with full-text extraction
- **3-Pass Gap Analysis** — Claim extraction, gap identification, scoring pipeline
- **Critic-Defender Idea Generation** — Adversarial loop: generate, critique, defend and refine
- **2-Pass Execution Planning** — Base plan + experiment configs, file structure, baselines
- **IEEE Paper Generation** — Full research paper with proper citations, DOCX and PDF export
- **SSE Real-time Streaming** — Live token streaming for plan and code generation
- **7 LLM Providers** — OpenAI, Anthropic, Groq, Gemini, Cohere, Ollama, OpenRouter
- **AES-256 Key Encryption** — API keys encrypted with Fernet before storage
- **Literature Review** — Automated literature review and annotated bibliography
- **Citation Graph** — Interactive citation network visualization
- **Plugin System** — Extensible architecture for third-party research tools
- **Interactive CLI** — Full workflow via command line

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.9+
- Node.js 18+
- (Optional) [Ollama](https://ollama.ai) for free local LLM models

### One-Command Setup

```bash
git clone https://github.com/Tharungowdapr/Research-IDE.git
cd Research-IDE
make setup    # Creates venv, installs deps, copies .env files
make dev      # Starts both backend and frontend
```

### Manual Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Edit with your keys
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

### Start Scripts

```bash
# Linux / macOS
chmod +x start.sh && ./start.sh

# Windows
start.bat
```

### Local URLs

| URL | Purpose |
|-----|---------|
| http://localhost:3000 | Frontend |
| http://localhost:8000/api/docs | Backend API docs (Swagger) |

### Configuration

**Backend** (`backend/.env`):

```env
DATABASE_URL=sqlite:///./research_ide.db
SECRET_KEY=your-random-secret-key
ENCRYPTION_KEY=your-32-char-encryption-key
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
GROQ_API_KEY=your-groq-key
ALLOWED_ORIGINS=["http://localhost:3000"]
```

Generate keys: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

**Frontend** (`frontend/.env.local`):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Cloud Deployment

The live version uses **Render** (backend) + **Vercel** (frontend) + **Neon** (PostgreSQL), all on free tiers.

### Backend (Render)

1. Push to GitHub, go to [render.com](https://render.com) > New Web Service
2. Connect repo, set:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Add environment variables in Render dashboard:
   ```
   DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/research_ide?sslmode=require
   SECRET_KEY=<fixed random string>
   ENCRYPTION_KEY=<fixed random string>
   DEFAULT_LLM_PROVIDER=groq
   GROQ_API_KEY=<your-key>
   ALLOWED_ORIGINS=["https://your-frontend.vercel.app"]
   ```

### Frontend (Vercel)

1. Go to [vercel.com](https://vercel.com) > Import Git Repository
2. Connect repo, set:
   - **Root Directory:** `frontend`
   - **Framework:** Next.js
3. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   ```

### Database (Neon)

1. Create free account at [neon.tech](https://neon.tech)
2. Create a project, copy the connection string
3. Paste as `DATABASE_URL` in Render dashboard

### Docker (Alternative)

```bash
docker-compose up --build
# Frontend: http://localhost:3000
# Backend: http://localhost:8000/api/docs
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (Next.js 14 / Vercel)              │
│                                                          │
│  Auth ─ Projects ─ Papers ─ Gaps ─ Ideas ─ Plan ─ Report │
│  (Zustand + persist)     (Axios + SSE streaming)        │
└──────────────────────────┬──────────────────────────────┘
                           │ REST API + SSE
┌──────────────────────────┴──────────────────────────────┐
│                Backend (FastAPI / Render)                 │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐  │
│  │ Auth     │  │ Pipeline │  │ Agents                │  │
│  │ JWT +    │  │ Intent,  │  │ Gap Miner, Idea Gen,  │  │
│  │ bcrypt   │  │ Retrieve │  │ Planner, Writer       │  │
│  └──────────┘  └──────────┘  └───────────────────────┘  │
│                                                          │
│  ┌──────────┐  ┌──────────────────────────────────────┐  │
│  │ Neon     │  │ LLM Client (7 providers)             │  │
│  │ Postgres │  │ Groq, OpenAI, Anthropic, Gemini, ... │  │
│  └──────────┘  └──────────────────────────────────────┘  │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
  ┌────────┴────────┐      ┌──────────┴──────────┐
  │ arXiv           │      │ Export Service      │
  │ Semantic Scholar│      │ PDF (fpdf2)         │
  │ OpenAlex        │      │ DOCX (python-docx)  │
  │ PapersWithCode  │      │ PPTX (python-pptx)  │
  └─────────────────┘      └─────────────────────┘
```

### Pipeline Flow

```
User Input
    │
    v
┌─────────────────┐
│ 1. Intent       │  Domain classification, keyphrases, NER
│    Extraction   │  (spaCy + pure-Python fallback)
└────────┬────────┘
         v
┌─────────────────┐
│ 2. Paper        │  arXiv, Semantic Scholar, OpenAlex, PwC
│    Retrieval    │  with full-text extraction + caching
└────────┬────────┘
         v
┌─────────────────┐
│ 3. Gap          │  3-pass: Claims → Gaps → Scoring
│    Analysis     │  (quality gate validated)
└────────┬────────┘
         v
┌─────────────────┐
│ 4. Idea         │  Critic-Defender adversarial loop
│    Generation   │  (quality gate validated)
└────────┬────────┘
         v
┌─────────────────┐
│ 5. Execution    │  2-pass: Base plan + enrichment
│    Planning     │  (SSE streaming)
└────────┬────────┘
         v
┌─────────────────┐
│ 6. Research     │  Guide, presentation slides (PPTX)
│    Guide        │
└────────┬────────┘
         v
┌─────────────────┐
│ 7. Report       │  IEEE-format paper with citations
│    Writing      │  (PDF + DOCX export)
└─────────────────┘
```

---

## Project Structure

```
Research-IDE/
├── backend/                        # FastAPI backend
│   ├── main.py                     # App entry + CORS + lifespan
│   ├── core/
│   │   ├── config.py               # Settings (env vars)
│   │   ├── database.py             # SQLAlchemy + engine
│   │   ├── security.py             # JWT, bcrypt, encryption
│   │   ├── llm_client.py           # Unified multi-provider LLM
│   │   ├── utils.py                # JSON parsing, rate limiter
│   │   ├── pdf_extractor.py        # PDF/HTML full text extraction
│   │   └── quality_gate.py         # AI output validation
│   ├── models/
│   │   ├── user.py                 # User + encrypted API keys
│   │   └── project.py              # Project, Output, PaperCache
│   ├── api/routes/
│   │   ├── auth.py                 # Register, login, refresh
│   │   ├── project.py              # CRUD for projects
│   │   ├── pipeline.py             # Intent, retrieval, full pipeline
│   │   ├── agents.py               # All agents + download endpoints
│   │   ├── llm_config.py           # API key management
│   │   ├── export.py               # Full project ZIP export
│   │   └── system.py               # System monitor
│   ├── services/
│   │   ├── nlp_analysis/           # NLP intent extraction
│   │   ├── retrieval/              # 4-source paper retrieval
│   │   ├── export_service.py       # PDF/DOCX/PPTX generation
│   │   └── citation_service.py     # Citation graph builder
│   ├── agents/
│   │   ├── gap_miner/              # 3-pass gap analysis
│   │   ├── idea_generator/         # Critic-Defender loop
│   │   ├── planner/                # 2-pass planning + SSE
│   │   ├── code_agent/             # Code scaffold + SSE
│   │   ├── writer/                 # IEEE paper generation
│   │   └── literature_review_agent.py
│   ├── tests/                      # 116 tests (pytest)
│   └── requirements.txt
│
├── frontend/                       # Next.js 14 frontend
│   ├── app/
│   │   ├── (app)/projects/[id]/    # 7-step project workflow
│   │   ├── auth/                   # Login, register
│   │   └── settings/               # LLM configuration
│   ├── components/                 # UI components
│   ├── services/api.ts             # API client (Axios + SSE)
│   ├── store/                      # Zustand state management
│   └── hooks/useStream.ts          # SSE streaming hook
│
├── cli/                            # Command-line interface
├── render.yaml                     # Render deployment config
├── docker-compose.yml              # Docker setup
├── Makefile                        # setup, dev, test, clean
├── start.sh / start.bat            # Quick start scripts
├── architecture.md                 # Developer knowledge base
├── CONTRIBUTING.md                 # Contribution guide
├── CHANGELOG.md                    # Version history
└── viva-qa.md                      # Evaluation Q&A
```

---

## Supported LLM Providers

| Provider | Models | API Key Required | Notes |
|----------|--------|-----------------|-------|
| **Ollama** | Any local model | No | Free, runs locally |
| **Groq** | Llama 3.3 70B, Mixtral | Yes | Ultra-fast inference |
| **OpenAI** | GPT-4o, GPT-4o Mini | Yes | Best quality |
| **Anthropic** | Claude Opus, Sonnet, Haiku | Yes | Great reasoning |
| **Google Gemini** | Gemini 1.5 Pro/Flash | Yes | 1M context window |
| **Cohere** | Command R+ | Yes | Good for RAG |
| **OpenRouter** | Many free models | Yes | Free tier available |

Switch providers in-app at **Settings > LLM Configuration** — no code changes required.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| **Backend** | FastAPI, SQLAlchemy 2.0, SQLite / PostgreSQL |
| **Frontend** | Next.js 14, Tailwind CSS, Zustand, TanStack Query, Axios |
| **NLP** | spaCy (with pure-Python fallback), KeyBERT (optional), SentenceTransformers (optional) |
| **Export** | fpdf2 (PDF), python-docx (DOCX), python-pptx (PPTX) |
| **Auth** | bcrypt, python-jose (JWT), Fernet (AES-256 key encryption) |
| **Deployment** | Render (backend), Vercel (frontend), Neon (PostgreSQL) |
| **CI/CD** | GitHub Actions |

---

## Testing

```bash
cd backend
python -m pytest tests/ -v
```

### Test Coverage (116 tests)

| Category | Tests | Status |
|----------|-------|--------|
| Retrieval Scoring | 12 | Pass |
| Deduplication | 4 | Pass |
| Quality Gate | 6 | Pass |
| Gap Analysis | 8 | Pass |
| Idea Generator | 3 | Pass |
| Intent Extraction | 5 | Pass |
| NLP Analyzer | 6 | Pass |
| Writer Agent | 9 | Pass |
| Rate Limiter | 2 | Pass |
| Export (PDF/DOCX) | 4 | Pass |
| LLM Client | 3 | Pass |
| Pipeline Integration | 2 | Pass |
| Scoring Metrics | 4 | Pass |
| Comprehensive | 42 | Pass |
| **Total** | **116** | **All pass** |

---

## CLI

```bash
cd backend
python -m cli.research_cli --help

# Login
python -m cli.research_cli login

# Create project
python -m cli.research_cli create-project \
  --title "NLP for Code Generation" \
  --input "Use transformer models to generate Python code"

# Run workflow interactively
python -m cli.research_cli workflow
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full CLI documentation.

---

## Security

- Passwords hashed with **bcrypt**
- API keys encrypted with **AES-256 (Fernet)**
- JWT tokens (access: 60 min, refresh: 7 days)
- CORS configured per deployment
- Rate limiting on auth endpoints (5 attempts / 15 min)

---

## License

[MIT](LICENSE)

---

**Tharun Gowda A P** (1RV23AI114) — RVCE 2025-26
