.PHONY: setup dev build test clean

setup:
	@echo "Setting up ResearchIDE..."
	cd backend && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install
	@[ -f backend/.env ] || cp backend/.env.example backend/.env
	@[ -f frontend/.env.local ] || cp frontend/.env.local.example frontend/.env.local
	@echo "Done. Run 'make dev' to start."

dev:
	@(cd backend && . venv/bin/activate && uvicorn main:app --reload --port 8000 &)
	@cd frontend && npm run dev

test:
	cd backend && . venv/bin/activate && python -m pytest tests/ -v

clean:
	rm -rf backend/venv backend/__pycache__ backend/*.db
	rm -rf frontend/node_modules frontend/.next
