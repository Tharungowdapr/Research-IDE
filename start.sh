#!/bin/bash
# =====================================================================
# ResearchIDE Quick Start Script
# Starts both backend and frontend for local development
# =====================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  ____                            _     ___ ____  _____"
echo " |  _ \ ___  ___  ___  __ _ _ __| |__ |_ _|  _ \| ____|"
echo " | |_) / _ \/ __|/ _ \/ _ | '__| '_ \ | || | | |  _|"
echo " |  _ <  __/\__ \  __/ (_| | |  | | | || || |_| | |___"
echo " |_| \_\___||___/\___|\__,_|_|  |_| |_|___|____/|_____|"
echo -e "${NC}"
echo -e "${GREEN}AI-Powered Research Assistant${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠ Python 3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠ Node.js not found. Please install Node.js 18+${NC}"
    exit 1
fi

# ── Backend Setup ─────────────────────────────────────────────────────────────
echo -e "\n${BLUE}[1/4] Setting up backend...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "  Installing dependencies..."
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
    echo "  Creating .env from example..."
    cp .env.example .env
fi

echo -e "${GREEN}  ✓ Backend ready${NC}"
cd ..

# ── Frontend Setup ────────────────────────────────────────────────────────────
echo -e "\n${BLUE}[2/4] Setting up frontend...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "  Installing npm packages..."
    npm install --quiet
fi

if [ ! -f ".env.local" ]; then
    echo "  Creating .env.local..."
    cp .env.local.example .env.local
fi

echo -e "${GREEN}  ✓ Frontend ready${NC}"
cd ..

# ── Start Services ────────────────────────────────────────────────────────────
echo -e "\n${BLUE}[3/4] Starting services...${NC}\n"

# Start backend in background
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

sleep 2

# Start frontend in background
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# ── Ready ─────────────────────────────────────────────────────────────────────
echo -e "\n${GREEN}[4/4] ResearchIDE is running!${NC}\n"
echo -e "  ${BLUE}Frontend:${NC}  http://localhost:3000"
echo -e "  ${BLUE}Backend:${NC}   http://localhost:8000"
echo -e "  ${BLUE}API Docs:${NC}  http://localhost:8000/api/docs"
echo ""
echo -e "${YELLOW}First time? Go to: http://localhost:3000/auth/register${NC}"
echo -e "${YELLOW}Then configure your LLM: http://localhost:3000/settings/llm${NC}"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo -e '\n${GREEN}Stopped.${NC}'; exit 0" SIGINT SIGTERM

wait
