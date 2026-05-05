# Contributing to ResearchIDE

Thank you for your interest in contributing! This guide covers everything you need.

## Quick Start

```bash
git clone https://github.com/your-username/research-ide
cd research-ide
make setup
make dev
```

## Branch Naming

Use Conventional Commits prefixes:
- `feature/your-feature-name` — new feature
- `fix/issue-description` — bug fix
- `docs/what-you-changed` — documentation only
- `refactor/what-you-changed` — code refactor, no behavior change
- `test/what-you-tested` — tests only

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Cohere provider support
fix: prevent crash when Ollama is offline
docs: update setup instructions for Windows
refactor: extract parse_llm_json to core/utils.py
test: add gap agent fallback tests
```

## Pull Request Workflow

1. Fork the repository
2. Create your branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `make test`
5. Commit: `git commit -m "feat: describe your change"`
6. Push: `git push origin feature/my-feature`
7. Open a Pull Request against `main`

## Running Tests Locally

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

## Code Style

- **Python**: Black formatter (`black .`), Ruff linter (`ruff check .`)
- **TypeScript**: ESLint (`npm run lint` in frontend/)
- Line length: 100 characters
- All new backend functions need a `_fallback_*` equivalent

## Adding a New LLM Provider

1. Add to `LLMProvider` enum in `backend/core/llm_client.py`
2. Add default model to `PROVIDER_DEFAULTS`
3. Add models list to `PROVIDER_MODELS`
4. Implement `_yourprovider_complete()` async method
5. Add to dispatcher in `complete()`
6. Add provider card to `backend/api/routes/llm_config.py`
7. Add tests

## Adding a New Agent

1. Create `backend/agents/your_agent/your_agent.py`
2. Add `__init__.py`
3. Export a `run_your_agent(...)` async function
4. Add `_fallback_*` function that returns valid data
5. Wire up in `backend/api/routes/agents.py`
6. Add frontend page if needed

## Reporting Issues

Include:
- OS and Python/Node version
- LLM provider being used
- Full error message and stack trace
- Steps to reproduce
