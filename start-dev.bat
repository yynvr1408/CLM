@echo off
REM CLM Platform - Manual Development Startup Script (Windows)
REM This script starts both backend and frontend servers in separate windows

setlocal enabledelayedexpansion

echo.
echo ============================================
echo  CLM Platform - Manual Development Setup
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 20+ from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if PostgreSQL is running
echo.
echo [1/4] Checking PostgreSQL connection...
psql -U clm_user -d clm_db -h localhost -c "SELECT 1" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Cannot connect to PostgreSQL database.
    echo Please ensure:
    echo   1. PostgreSQL is running
    echo   2. User 'clm_user' exists with password 'clm_password'
    echo   3. Database 'clm_db' exists
    echo.
    echo See MANUAL_SETUP_GUIDE.md for database setup instructions.
    pause
    exit /b 1
)
echo ✓ PostgreSQL connection successful

REM Check and create .env if needed
echo.
echo [2/4] Checking environment configuration...
if not exist ".env" (
    echo WARNING: .env file not found. Creating with defaults...
    (
        echo # Database connection
        echo DATABASE_URL="postgresql://clm_user:clm_password@localhost:5432/clm_db"
        echo.
        echo # JWT and Security
        echo DEBUG=True
        echo SECRET_KEY="dev-secret-key-change-in-production"
        echo ALGORITHM="HS256"
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo.
        echo # Email (optional^)
        echo SMTP_HOST="smtp.gmail.com"
        echo SMTP_PORT=587
        echo SMTP_USER=""
        echo SMTP_PASSWORD=""
        echo.
        echo # CORS
        echo CORS_ORIGINS=["http://localhost:5173","http://localhost:8000"]
        echo ALLOWED_HOSTS=["localhost","127.0.0.1"]
        echo.
        echo # Frontend
        echo VITE_API_URL="http://localhost:8000/api/v1"
    ) > .env
    echo ✓ Created .env file
) else (
    echo ✓ .env file exists
)

REM Backend setup
echo.
echo [3/4] Setting up Backend...
cd backend
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment and installing packages...
call venv\Scripts\activate.bat
pip install -q -r requirements.txt >nul 2>&1
echo ✓ Backend ready

REM Start backend in new window
echo.
echo [4/4] Starting services...
echo.
start "CLM Backend (FastAPI)" cmd /k "cd %cd% && venv\Scripts\activate.bat && python -m uvicorn main:app --reload --port 8000"
echo ✓ Backend server starting in new window (http://localhost:8000)

REM Go back to root and setup frontend
cd ..
if not exist "node_modules" (
    echo Installing frontend packages...
    call npm install -q
)

REM Start frontend in new window
start "CLM Frontend (React)" cmd /k "npm run dev"
echo ✓ Frontend server starting in new window (http://localhost:5173)

echo.
echo ============================================
echo  Services Starting...
echo ============================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/api/docs
echo.
echo Press any key in each terminal window to continue with the server...
echo.
pause
