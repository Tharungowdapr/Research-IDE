.PHONY: setup dev test clean help

help:
	@echo "ResearchIDE — Available commands:"
	@echo "  make setup   Install all dependencies"
	@echo "  make dev     Start backend + frontend"
	@echo "  make test    Run backend tests"
	@echo "  make clean   Remove generated files"

setup:
	@echo "Setting up backend..."
	cd backend && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	@echo "Setting up frontend..."
	cd frontend && npm install
	@[ -f backend/.env ] || cp backend/.env.example backend/.env
	@[ -f frontend/.env.local ] || cp frontend/.env.local.example frontend/.env.local
	@echo ""
	@echo "✅ Setup complete! Run 'make dev' to start."
	@echo "   Then visit: http://localhost:3000/auth/register"
	@echo "   Configure AI: http://localhost:3000/settings/llm"

dev:
	@(cd backend && . venv/bin/activate && uvicorn main:app --reload --port 8000 &)
	@echo "Backend started on http://localhost:8000"
	@cd frontend && npm run dev

test:
	cd backend && . venv/bin/activate && python -m pytest tests/ -v --tb=short

clean:
	rm -rf backend/venv backend/__pycache__ backend/research_ide.db
	rm -rf frontend/node_modules frontend/.next
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
