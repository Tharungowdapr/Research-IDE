# 🧠 ResearchIDE

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python) ![Node](https://img.shields.io/badge/Node-18+-green?logo=node.js) ![License](https://img.shields.io/badge/License-MIT-yellow) ![CI](https://github.com/Tharungowdapr/Research-IDE/actions/workflows/ci.yml/badge.svg)

**AI-Powered Research Assistant** — From research question to paper, code, and report in 7 guided steps.

---

## ✨ Features

- [x] **NLP Intent Extraction** — AI extracts domain, keywords, constraints from your research description
- [x] **Multi-Source Paper Retrieval** — Fetches from arXiv, Semantic Scholar, OpenAlex, and PapersWithCode
- [x] **3-Pass Gap Analysis** — Claim extraction → Gap identification → Scoring pipeline
- [x] **Critic-Defender Idea Generation** — Adversarial loop: Generate → Critique → Defend & Refine
- [x] **2-Pass Execution Planning** — Base plan + experiment configs, file structure, baselines
- [x] **12-File Code Scaffold** — Complete runnable project with wandb, PyYAML, pytest, Makefile
- [x] **SSE Real-time Streaming** — Live token streaming for Plan and Code generation
- [x] **High-Capacity Research** — Scaled to 15+ gaps and 10+ ideas per project
- [x] **IEEE Paper Generation** — Full research paper with proper citations and references
- [x] **DOCX & PDF Export** — Download IEEE-format papers as Word or PDF documents
- [x] **7 LLM Providers** — OpenAI, Anthropic, Groq, Gemini, Cohere, Ollama (free), OpenRouter
- [x] **AES-256 Key Encryption** — API keys encrypted before storage

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/Tharungowdapr/Research-IDE.git
cd Research-IDE

# One-command setup
make setup

# Start development servers
make dev
```

Or use the start scripts:

```bash
# Linux / macOS
chmod +x start.sh && ./start.sh

# Windows
start.bat
```

### Prerequisites

- Python 3.9+
- Node.js 18+
- (Optional) [Ollama](https://ollama.ai) for free local models

---

## 🌐 Access

| URL | Purpose |
|-----|---------|
| http://localhost:3000 | Frontend (main app) |
| http://localhost:8000/api/docs | Backend API docs (Swagger) |

---

## 🤖 Supported LLM Providers

| Provider | Models | API Key | Notes |
|----------|--------|---------|-------|
| **Ollama** | Any local model | ❌ No | Free, runs locally |
| **OpenAI** | GPT-4o, GPT-4o Mini | ✅ Yes | Best quality |
| **Anthropic** | Claude Opus, Sonnet, Haiku | ✅ Yes | Great reasoning |
| **Groq** | Llama 3.3 70B, Mixtral | ✅ Yes | Ultra-fast |
| **Google Gemini** | Gemini 1.5 Pro/Flash | ✅ Yes | 1M context |
| **Cohere** | Command R+ | ✅ Yes | Great for RAG |
| **OpenRouter** | Many free models | ✅ Yes | Free tier |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14)              │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │
│  │Input │→│Papers│→│ Gaps │→│Ideas │→│ Plan │→...    │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘       │
└────────────────────────┬─────────────────────────────┘
                         │ REST API
┌────────────────────────┴─────────────────────────────┐
│                  Backend (FastAPI)                     │
│  ┌─────────┐  ┌──────────┐  ┌─────────────────────┐  │
│  │ Auth    │  │ Pipeline │  │ Agents              │  │
│  │ (JWT)   │  │ (Intent, │  │ (Gap, Idea, Plan,   │  │
│  │         │  │  Retrieve)│  │  Code, Report)      │  │
│  └─────────┘  └──────────┘  └─────────────────────┘  │
│  ┌─────────┐  ┌──────────────────────────────────┐   │
│  │ SQLite  │  │ LLM Client (7 providers)         │   │
│  │ + Cache │  │ OpenAI/Anthropic/Groq/Gemini/... │   │
│  └─────────┘  └──────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
         │                          │
    ┌────┴────┐          ┌──────────┴──────────┐
    │ arXiv   │          │ SSE Streaming       │
    │ OpenAlex│          │ (Real-time Live UI) │
    └─────────┘          └─────────────────────┘
```

---

## 🗂️ Project Structure

```
research-ide/
├── backend/                    # FastAPI backend
│   ├── main.py                 # App entry point
│   ├── core/
│   │   ├── config.py           # Settings (env vars)
│   │   ├── database.py         # SQLAlchemy setup
│   │   ├── security.py         # JWT, bcrypt, encryption
│   │   └── llm_client.py       # Unified multi-provider LLM client
│   ├── models/
│   │   ├── user.py             # User model
│   │   └── project.py          # Project, Output, PaperCache models
│   ├── api/routes/
│   │   ├── auth.py             # Register, login, refresh
│   │   ├── project.py          # CRUD for projects
│   │   ├── pipeline.py         # Intent extraction, retrieval
│   │   ├── agents.py           # All agents + DOCX/PDF download
│   │   └── llm_config.py       # API key management
│   ├── services/
│   │   ├── intent/             # NLP intent extraction
│   │   ├── retrieval/          # 4-source paper retrieval
│   │   └── export_service.py   # DOCX/PDF generation
│   ├── agents/
│   │   ├── gap_miner/          # 3-pass gap analysis
│   │   ├── idea_generator/     # Critic-Defender loop
│   │   ├── planner/            # 2-pass planning
│   │   ├── code_agent/         # 12-file scaffold
│   │   └── writer/             # IEEE paper generation
│   ├── tests/                  # Pytest tests
│   ├── scripts/                # Database seeding
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/                   # Next.js 14 frontend
│   ├── app/
│   │   ├── (app)/              # Protected routes
│   │   │   ├── dashboard/
│   │   │   ├── projects/       # 7-step project workflow
│   │   │   └── settings/       # LLM configuration
│   │   └── auth/               # Login, register
│   ├── services/api.ts         # API client
│   ├── store/useAuthStore.ts   # Auth state (Zustand)
│   └── components/
│
├── .github/workflows/ci.yml   # GitHub Actions CI
├── Makefile                    # Setup, dev, test, clean
├── CONTRIBUTING.md
├── docker-compose.yml
├── start.sh / start.bat
└── README.md
```

---

## ⚙️ Configuration

### Backend (`backend/.env`)

```env
DATABASE_URL=sqlite:///./research_ide.db
SECRET_KEY=your-long-random-secret-key-here
ENCRYPTION_KEY=your-32-char-encryption-key-here
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🔐 Security

- Passwords hashed with **bcrypt**
- API keys encrypted with **AES-256 (Fernet)**
- JWT tokens (access: 60min, refresh: 7 days)
- CORS configured for frontend origin only

---

## 🛠️ Tech Stack

| Layer | Tools |
|-------|-------|
| **Backend** | FastAPI, SQLAlchemy, SQLite, bcrypt, python-jose, httpx |
| **Frontend** | Next.js 14, Tailwind CSS, Zustand, TanStack Query, Axios |
| **Export** | python-docx (DOCX), WeasyPrint (PDF) |
| **CI/CD** | GitHub Actions |

---

## 🧪 Development

```bash
# Run tests
make test

# Run only backend
cd backend && source venv/bin/activate && uvicorn main:app --reload

# Run only frontend
cd frontend && npm run dev

# Reset database
rm backend/research_ide.db  # Restart backend — tables auto-recreate
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [arXiv API](https://arxiv.org/help/api) for paper search
- [Semantic Scholar API](https://api.semanticscholar.org/) for citations
- [OpenAlex](https://openalex.org/) for open scholarly metadata
- [Papers With Code](https://paperswithcode.com/) for code references
- [Ollama](https://ollama.ai) for local model serving