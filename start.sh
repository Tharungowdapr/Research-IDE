#!/bin/bash
set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; RED='\033[0;31m'; NC='\033[0m'

echo -e "${BLUE}"
echo "  ____                            _     ___ ____  _____"
echo " |  _ \\ ___  ___  ___  __ _ _ __| |__ |_ _|  _ \\| ____|"
echo " | |_) / _ \\/ __|/ _ \\/ _\` | '__| '_ \\ | || | | |  _|"
echo " |  _ <  __/\\__ \\  __/ (_| | |  | | | || || |_| | |___"
echo " |_| \\_\\___||___/\\___|\\__,_|_|  |_| |_|___|____/|_____|"
echo -e "${NC}"
echo -e "${GREEN}ResearchIDE v2.1${NC}"
echo ""

# WeasyPrint system deps check
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! ldconfig -p 2>/dev/null | grep -q libpango; then
        echo -e "${YELLOW}⚠  WeasyPrint PDF needs system libs. Run:${NC}"
        echo -e "   ${YELLOW}sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 libcairo2 libffi-dev${NC}"
        echo -e "   ${YELLOW}(PDF download will return an error without these. DOCX and Markdown still work.)${NC}"
        echo ""
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v pango-view &>/dev/null && ! brew list pango &>/dev/null 2>&1; then
        echo -e "${YELLOW}⚠  WeasyPrint PDF needs Pango on macOS. Run:${NC}"
        echo -e "   ${YELLOW}brew install pango${NC}"
        echo -e "   ${YELLOW}(PDF download will return an error without this. DOCX and Markdown still work.)${NC}"
        echo ""
    fi
fi

command -v python3 &>/dev/null || { echo -e "${RED}✗ Python 3 not found${NC}"; exit 1; }
command -v node &>/dev/null    || { echo -e "${RED}✗ Node.js not found${NC}"; exit 1; }

echo -e "${BLUE}[1/4] Setting up backend...${NC}"
cd backend
[ ! -d "venv" ] && python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt
[ ! -f ".env" ] && cp .env.example .env
echo -e "${GREEN}  ✓ Backend ready${NC}"
cd ..

echo -e "\n${BLUE}[2/4] Setting up frontend...${NC}"
cd frontend
[ ! -d "node_modules" ] && npm install --quiet
[ ! -f ".env.local" ] && cp .env.local.example .env.local
echo -e "${GREEN}  ✓ Frontend ready${NC}"
cd ..

echo -e "\n${BLUE}[3/4] Starting services...${NC}"
cd backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..
sleep 2

cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "\n${GREEN}[4/4] ResearchIDE is running!${NC}\n"
echo -e "  ${BLUE}Frontend:${NC}  http://localhost:3000"
echo -e "  ${BLUE}Backend:${NC}   http://localhost:8000"
echo -e "  ${BLUE}API Docs:${NC}  http://localhost:8000/api/docs"
echo ""
echo -e "${YELLOW}First time? → http://localhost:3000/auth/register${NC}"
echo -e "${YELLOW}Then set AI → http://localhost:3000/settings/llm${NC}"
echo ""
echo "Press Ctrl+C to stop all services"
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo -e '\n${GREEN}Stopped.${NC}'; exit 0" SIGINT SIGTERM
wait
