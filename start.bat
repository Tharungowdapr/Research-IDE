@echo off
echo.
echo  ____                            _     ___ ____  _____
echo ^|  _ \ ___  ___  ___  __ _ _ __^| ^|__ ^|_ _^|  _ \^| ____^|
echo ^| ^|_) / _ \/ __^|/ _ \/ _` ^| '__^| '_ \ ^| ^|^| ^| ^| ^|  _^|
echo ^| ^|  ^< ^| /_) ^|(__^|  __/ (_^| ^| ^|  ^| ^| ^| ^| ^|^| ^|_^| ^| ^|___
echo ^|_^| \_\___^|^|___/\___^|\__,_^|_^|  ^|_^| ^|_^|___^|____/^|^|___^|^|
echo.
echo AI-Powered Research Assistant
echo.

:: Backend setup
echo [1/4] Setting up backend...
cd backend

if not exist "venv" (
    echo   Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
echo   Installing dependencies...
pip install -q -r requirements.txt

if not exist ".env" (
    copy .env.example .env
    echo   Created .env from example
)

echo [OK] Backend ready
cd ..

:: Frontend setup
echo.
echo [2/4] Setting up frontend...
cd frontend

if not exist "node_modules" (
    echo   Installing npm packages...
    npm install --quiet
)

if not exist ".env.local" (
    copy .env.local.example .env.local
    echo   Created .env.local
)

echo [OK] Frontend ready
cd ..

:: Start backend
echo.
echo [3/4] Starting backend...
start "ResearchIDE Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak > nul

:: Start frontend
echo [4/4] Starting frontend...
start "ResearchIDE Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================
echo  ResearchIDE is starting!
echo ============================================
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/api/docs
echo ============================================
echo   First time? Register at:
echo   http://localhost:3000/auth/register
echo   Then set up AI at:
echo   http://localhost:3000/settings/llm
echo ============================================
pause
