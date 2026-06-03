.PHONY: setup dev test clean cli-install

setup:
	python3 -m venv backend/venv && \
	. backend/venv/bin/activate && \
	pip install -q -r backend/requirements.txt && \
	cd frontend && npm install --quiet
	@if [ ! -f backend/.env ]; then cp backend/.env.example backend/.env; fi
	@if [ ! -f frontend/.env.local ]; then cp frontend/.env.local.example frontend/.env.local; fi
	@echo "✓ Setup complete. Run 'make dev' to start."

dev:
	@echo "Starting backend..."
	. backend/venv/bin/activate && uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
	@sleep 2
	@echo "Starting frontend..."
	cd frontend && npm run dev &

test:
	. backend/venv/bin/activate && cd backend && python -m pytest tests/ -v

cli-install:
	pip install -e cli/

clean:
	rm -rf backend/venv backend/__pycache__ backend/**/__pycache__ backend/*.db
	rm -rf frontend/node_modules frontend/.next
