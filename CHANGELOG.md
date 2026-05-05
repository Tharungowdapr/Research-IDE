# Changelog

All notable changes to ResearchIDE are documented here.

## [2.2.0] — 2026-04-29

### Bug Fixes
- **PapersWithCode `github_url`** — fixed: API returns `repositories` (list), not `repository` (dict)
- **DOCX/PDF ownership check** — download endpoints now verify project belongs to requesting user
- **Planner Pass 1 save** — base plan saved immediately via callback; Pass 2 enrichment failure no longer kills whole plan
- **Gap analysis context** — adaptive claim count: 20 claims for Ollama, 35 for cloud models; claim text truncated to 150 chars
- **OpenAlex 429** — retry with 2s backoff on rate limit before giving up
- **Dataset fallback** — `dataset.py` now generates a working dummy dataset instead of raising `RuntimeError` when HuggingFace dataset not found
- **F-string escaping** — fixed double-brace escaping in `dataset.py` template inside Python f-strings
- **Token refresh in downloads** — download handler reads fresh token via `useAuthStore.getState()` at call time, not stale render-time capture
- **macOS WeasyPrint detection** — `start.sh` now detects `darwin` and prints `brew install pango` instruction
- **`useStream` hook** — rewritten cleanly: no self-recursion, proper `AbortController`, token refresh with `refreshAccessToken()` helper

### New Features

#### Backend
- `PATCH /api/projects/{id}/input` — edit research description + reset all outputs
- `GET /api/agents/more-ideas` — generate 4 additional ideas beyond current set
- `POST /api/pipeline/papers/add` — add a paper manually (title, abstract, authors, year, URL)
- `GET /api/pipeline/stream/{id}/intent` — SSE streaming intent extraction with live progress
- `GET /api/pipeline/stream/{id}/retrieve` — SSE streaming paper retrieval (was already added in v2.1)
- `GET /api/projects/{id}/history/{output_type}` — get version history for any output
- `OutputHistory` database table — archives previous versions before overwriting

#### Frontend
- **Edit research description** — inline edit button on input page with save/cancel, clears all outputs
- **Streaming intent extraction** — live progress log while AI analyzes your description
- **Project search + filter** — search by title/content, filter by stage badge on projects list
- **Syntax highlighting** — `react-syntax-highlighter` with `vscDarkPlus` theme in code viewer, line numbers, language detection
- **"Generate 4 more ideas"** button on ideas page — runs adversarial pipeline again, merges results
- **"Add paper manually" modal** on papers page — form for title, abstract, authors, year, URL
- **Dark/light mode toggle** — Sun/Moon button in sidebar, persisted via Zustand, applied via `data-theme` attribute
- **Output version history** — previous outputs archived before overwrite; accessible via API
- **Favicon** — SVG brand icon in browser tab
- **404 redirect** — invalid project IDs redirect to `/projects` instead of crashing

### Quality Improvements
- `StreamLog` shared component eliminates 200+ lines of duplicate inline log code across pages
- All 7 project step pages wrapped in `ErrorBoundary` — render crashes show "Try Again" instead of white screen
- Mobile responsive: sidebar `hidden lg:flex`, main `lg:ml-60`, paper explorer `lg:col-span-*`
- `formatDistanceToNow` null guard prevents crash on new projects with null `updated_at`
- Papers page: "Add Paper" button when search returns no results
- Planner page: shows `experiment_configs`, `file_structure`, `baseline_implementations` from v2 planner

## [2.1.0] — 2026-04-28

### Bug Fixes
- `useStream` hook: proper `AbortController`, token refresh, no self-recursion
- `StreamLog`: shared component across all step pages
- Report page double-trigger race: `useRef` debounce
- `github_url` passed from papers to code agent (was checking idea dict which never had it)
- `formatDistanceToNow` null guard on `updated_at`
- Invalid project 404: redirects to `/projects`

### New Features
- Streaming SSE on ideas, planner, code, report pages
- `ErrorBoundary` on all step pages
- Mobile responsive layout
- Ollama offline banner on dashboard
- `LICENSE` MIT file
- SVG favicon

## [2.0.0] — 2026-04-26

### Major upgrade from v1.0
- 4-source paper retrieval: arXiv + Semantic Scholar + OpenAlex + PapersWithCode
- Relevance scoring and re-ranking
- 3-pass gap analysis with claim extraction
- Critic-Defender adversarial idea generation
- 2-pass planner with experiment configs
- 12-file runnable code scaffold
- IEEE-format paper with DOCX + PDF download
- SSE streaming on all agent steps
- GitHub Actions CI, Makefile, pyproject.toml

## [1.0.0] — 2026-04-20

### Initial release
- 7-step research workflow
- 7 LLM providers with encrypted key storage
- Auth with bcrypt + JWT
- SQLite + PostgreSQL support
- Docker + docker-compose
