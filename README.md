# 🧠 ResearchIDE

**AI-Powered Research Assistant** — From research question to paper, code, and report in 7 guided steps.

---

## ✨ What It Does

ResearchIDE is a full-stack web application that guides researchers through the entire research lifecycle:

1. **Input & NLP Analysis** — Describe your idea; AI extracts domain, keywords, constraints, and search queries
2. **Paper Retrieval** — Automatically fetches relevant papers from arXiv and Semantic Scholar
3. **Gap Analysis** — AI identifies research gaps, limitations, and opportunities in the literature
4. **Idea Generation** — Generates ranked, scored research ideas with novelty and feasibility scores
5. **Execution Planning** — Creates a detailed project plan with phases, tech stack, and timeline
6. **Code Generation** — Generates starter code with model, training loop, and setup instructions
7. **Paper Writing** — Produces a structured research paper draft with abstract, sections, and references

---

## 🤖 Supported LLM Providers

| Provider | Models | API Key Required | Notes |
|----------|--------|-----------------|-------|
| **Ollama** | Any local model | ❌ No | Run models locally, 100% free |
| **OpenAI** | GPT-4o, GPT-4o Mini, GPT-3.5 | ✅ Yes | Best quality |
| **Anthropic** | Claude Opus 4.5, Sonnet 4.5, Haiku | ✅ Yes | Great for reasoning |
| **Groq** | Llama 3.3 70B, Mixtral | ✅ Yes | Ultra-fast inference |
| **Google Gemini** | Gemini 1.5 Pro/Flash | ✅ Yes | 1M token context |
| **Cohere** | Command R+ | ✅ Yes | Great for RAG |
| **OpenRouter** | Many models (free tier available) | ✅ Yes | Access free models |

**API keys are encrypted with AES-256 before storage.** Keys are never logged or exposed.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- (Optional) [Ollama](https://ollama.ai) for local free models

### Option 1: One-Command Start (Recommended)

**Linux / macOS:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```
start.bat
```

This will:
- Create Python virtual environment
- Install all backend dependencies
- Install all frontend dependencies
- Start both servers

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Edit as needed
uvicorn main:app --reload --port 8000
```

**Frontend (separate terminal):**
```bash
cd frontend
npm install
cp .env.local.example .env.local  # Edit as needed
npm run dev
```

### Option 3: Docker

```bash
docker-compose up --build
```

---

## 🌐 Access

| URL | Purpose |
|-----|---------|
| http://localhost:3000 | Frontend (main app) |
| http://localhost:8000/api/docs | Backend API docs (Swagger) |
| http://localhost:8000/api/health | Health check |

---

## 🦙 Using Ollama (Free, Local, No API Key)

1. **Install Ollama:** https://ollama.ai
2. **Pull a model:**
   ```bash
   ollama pull llama3.2          # Fast, good quality (2GB)
   ollama pull llama3.1:70b      # Best quality (40GB, needs GPU)
   ollama pull mistral           # Great alternative (4GB)
   ollama pull phi3              # Lightweight (2GB)
   ```
3. **Verify Ollama is running:** http://localhost:11434
4. In ResearchIDE → **AI Settings** → Select **Ollama** → Your models appear automatically

---

## 🔑 Getting API Keys

| Provider | Free Tier | Sign Up |
|----------|-----------|---------|
| OpenAI | $5 credit for new accounts | https://platform.openai.com/api-keys |
| Anthropic | $5 credit for new accounts | https://console.anthropic.com/account/keys |
| Groq | **Free tier available** | https://console.groq.com/keys |
| Google Gemini | **Free tier available** | https://aistudio.google.com/app/apikey |
| Cohere | **Free tier available** | https://dashboard.cohere.com/api-keys |
| OpenRouter | **Free models available** | https://openrouter.ai/keys |

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
│   │   ├── user.py             # User SQLAlchemy model
│   │   └── project.py          # Project, Output models
│   ├── api/routes/
│   │   ├── auth.py             # Register, login, refresh
│   │   ├── project.py          # CRUD for projects
│   │   ├── pipeline.py         # Intent extraction, retrieval
│   │   ├── agents.py           # Gap analysis, ideas, plan, code, report
│   │   └── llm_config.py       # API key management, model selection
│   ├── services/
│   │   ├── intent/             # NLP intent extraction
│   │   └── retrieval/          # arXiv + Semantic Scholar fetch
│   ├── agents/
│   │   ├── gap_miner/          # Research gap analysis
│   │   ├── idea_generator/     # Idea generation + scoring
│   │   ├── planner/            # Execution planning
│   │   ├── code_agent/         # Code generation
│   │   └── writer/             # Paper/report writing
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                   # Next.js 14 frontend
│   ├── app/
│   │   ├── (app)/              # Protected routes (need auth)
│   │   │   ├── dashboard/      # Main dashboard
│   │   │   ├── projects/       # Project list + new project
│   │   │   │   └── [id]/       # Project pages (7 steps)
│   │   │   │       ├── input/  # NLP analysis view
│   │   │   │       ├── papers/ # Paper explorer
│   │   │   │       ├── gaps/   # Gap analysis
│   │   │   │       ├── ideas/  # Idea cards
│   │   │   │       ├── planner/# Execution plan
│   │   │   │       ├── code/   # Code viewer
│   │   │   │       └── report/ # Paper writer
│   │   │   └── settings/
│   │   │       └── llm/        # AI model configuration (KEY FEATURE)
│   │   └── auth/               # Login, register pages
│   ├── components/layout/      # Sidebar
│   ├── services/api.ts         # Axios API client
│   ├── store/useAuthStore.ts   # Zustand auth state
│   ├── store/useAuthStore.ts   # Zustand auth state
│   └── package.json
│
├── docker-compose.yml
├── start.sh                    # Linux/Mac start script
├── start.bat                   # Windows start script
└── README.md
```

---

## ⚙️ Configuration

### Backend (`backend/.env`)

```env
# Database — SQLite works out of the box, no setup needed
DATABASE_URL=sqlite:///./research_ide.db

# Security — CHANGE THESE IN PRODUCTION
SECRET_KEY=your-long-random-secret-key-here
ENCRYPTION_KEY=your-32-char-encryption-key-here

# Default LLM (used if user hasn't set preferences)
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

- Passwords hashed with **bcrypt** (never stored plain)
- API keys encrypted with **AES-256 (Fernet)** before database storage
- JWT tokens for auth (access: 60min, refresh: 7 days)
- Keys never appear in logs or API responses
- CORS configured to only allow frontend origin

---

## 🛠️ Tech Stack

### Backend
| Tool | Purpose |
|------|---------|
| FastAPI | REST API framework |
| SQLAlchemy | ORM |
| SQLite / PostgreSQL | Database |
| bcrypt | Password hashing |
| python-jose | JWT tokens |
| cryptography (Fernet) | API key encryption |
| httpx | Async HTTP (LLM API calls) |

### Frontend
| Tool | Purpose |
|------|---------|
| Next.js 14 | React framework |
| Tailwind CSS | Styling |
| Zustand | Global state (auth) |
| TanStack Query | Server state |
| Axios | HTTP client |
| Lucide React | Icons |

---

## 🧪 Development Tips

### Run only backend:
```bash
cd backend && source venv/bin/activate && uvicorn main:app --reload
```

### Run only frontend:
```bash
cd frontend && npm run dev
```

### View API docs:
http://localhost:8000/api/docs (Swagger UI)

### Reset database:
```bash
rm backend/research_ide.db
# Restart backend — tables auto-recreate
```

### Switch to PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/research_ide
```

---

## 🤝 Adding a New LLM Provider

1. Add to `LLMProvider` enum in `backend/core/llm_client.py`
2. Add default model to `PROVIDER_DEFAULTS`
3. Add models list to `PROVIDER_MODELS`
4. Implement `_yourprovider_complete()` method
5. Add to dispatcher dict in `complete()`
6. Add provider card to `backend/api/routes/llm_config.py`

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [arXiv API](https://arxiv.org/help/api) for paper search
- [Semantic Scholar API](https://api.semanticscholar.org/) for citations and metadata
- [Ollama](https://ollama.ai) for local model serving
- All the amazing LLM providers