# ResearchIDE

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Node 18+](https://img.shields.io/badge/Node-18+-green.svg)](https://nodejs.org)
[![License MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/your-username/research-ide/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/research-ide/actions)

AI-powered research assistant — from a research question to a full IEEE paper, working code, and execution plan.

## Clone & Run in 3 Commands

```bash
git clone https://github.com/your-username/research-ide
cd research-ide
make setup && make dev
```

Then open **http://localhost:3000/auth/register**, and go to **Settings → AI Settings** to configure your LLM.

## What It Does

7 guided steps per project:

- [x] **NLP Analysis** — extracts domain, keywords, constraints, search queries
- [x] **Paper Retrieval** — fetches from arXiv, Semantic Scholar, OpenAlex, PapersWithCode (up to 25 papers, relevance-ranked)
- [x] **Gap Analysis** — 3-pass pipeline: claim extraction → gap identification → addressability scoring
- [x] **Idea Generation** — Critic-Defender adversarial loop: generate → critique → refine → rank top 4
- [x] **Execution Planning** — phases, tech stack, experiment configs, file structure
- [x] **Code Generation** — 12-file runnable scaffold (model, training loop, eval, Makefile, tests)
- [x] **Paper Writing** — IEEE-format draft with citations; download as **DOCX** or **PDF**

## Architecture

```
[Next.js 14 Frontend]
         ↓ REST + SSE streaming
[FastAPI Backend]
    ├── NLP Intent Service
    ├── 4-Source Paper Retrieval
    ├── Gap Mining Agent (3-pass)
    ├── Idea Generator (Critic-Defender)
    ├── Planner Agent (2-pass)
    ├── Code Agent (12-file scaffold)
    ├── Writer Agent (IEEE format)
    └── Download Service (DOCX + PDF)
         ↓
[SQLite / PostgreSQL]
```

## Supported LLM Providers

| Provider | Free Option | Get Key |
|---|---|---|
| 🦙 Ollama (Local) | ✅ 100% free | [ollama.ai](https://ollama.ai) |
| ⚡ Groq | ✅ Free tier | [console.groq.com](https://console.groq.com/keys) |
| ✨ Google Gemini | ✅ Free tier | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| 🔀 OpenRouter | ✅ Free models | [openrouter.ai](https://openrouter.ai/keys) |
| 🤖 OpenAI | $5 credit | [platform.openai.com](https://platform.openai.com/api-keys) |
| 🧠 Anthropic | $5 credit | [console.anthropic.com](https://console.anthropic.com/account/keys) |
| 🌊 Cohere | ✅ Free tier | [dashboard.cohere.com](https://dashboard.cohere.com/api-keys) |

## Commands

```bash
make setup    # Install all deps, copy .env files
make dev      # Start backend (8000) + frontend (3000)
make test     # Run pytest suite
make clean    # Remove venv, node_modules, DB
```

## API Docs

Available at **http://localhost:8000/api/docs** while backend is running.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs welcome.

## License

MIT — see [LICENSE](LICENSE).
