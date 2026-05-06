# Contributing to ResearchIDE

Thank you for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/Research-IDE.git
cd Research-IDE

# Setup
make setup

# Run dev servers
make dev
```

## Workflow

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature`
3. **Make changes** and test locally
4. **Commit** with clear messages (see below)
5. **Push** to your fork: `git push origin feature/your-feature`
6. **Open a Pull Request** against `main`

## Commit Message Format

```
type(scope): description

feat(agents): add 3-pass gap analysis pipeline
fix(retrieval): handle OpenAlex null abstracts
docs(readme): update setup instructions
test(agents): add fallback function tests
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`

## Code Style

### Backend (Python)
- Formatter: `black` (line-length: 100)
- Linter: `ruff`
- Type hints encouraged
- All agent functions must have a `_fallback_*()` equivalent

### Frontend (TypeScript)
- Use existing CSS variable system (`var(--bg-card)`, `var(--border)`, etc.)
- Use existing utility classes (`btn-primary`, `card`, `badge-blue`, etc.)
- Components must be responsive

## Testing

```bash
# Backend tests
cd backend && source venv/bin/activate && python -m pytest tests/ -v

# Frontend build check
cd frontend && npm run build
```

## Architecture Rules

- **Do not change**: database schema, auth system, LLM client, settings pages
- All agent outputs saved to `outputs` table with `output_type` string key
- All new endpoints require auth: `current_user: User = Depends(get_current_user)`
- All HTTP calls use `httpx.AsyncClient` with timeouts

## Questions?

Open an issue or start a discussion. We're happy to help!
