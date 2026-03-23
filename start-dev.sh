#!/bin/bash

# CLM Platform - Manual Development Startup Script (Linux/Mac)
# This script starts both backend and frontend servers

echo ""
echo "============================================"
echo " CLM Platform - Manual Development Setup"
echo "============================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found. Please install Python 3.11+"
    echo "Visit: https://www.python.org/"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found. Please install Node.js 20+"
    echo "Visit: https://nodejs.org/"
    exit 1
fi

# Check if PostgreSQL is running
echo ""
echo "[1/4] Checking PostgreSQL connection..."
if ! psql -U clm_user -d clm_db -h localhost -c "SELECT 1" &> /dev/null; then
    echo "ERROR: Cannot connect to PostgreSQL database."
    echo "Please ensure:"
    echo "  1. PostgreSQL is running"
    echo "  2. User 'clm_user' exists with password 'clm_password'"
    echo "  3. Database 'clm_db' exists"
    echo ""
    echo "See MANUAL_SETUP_GUIDE.md for database setup instructions."
    exit 1
fi
echo "✓ PostgreSQL connection successful"

# Check and create .env if needed
echo ""
echo "[2/4] Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found. Creating with defaults..."
    cat > .env << 'EOF'
# Database connection
DATABASE_URL="postgresql://clm_user:clm_password@localhost:5432/clm_db"

# JWT and Security
DEBUG=True
SECRET_KEY="dev-secret-key-change-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (optional)
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER=""
SMTP_PASSWORD=""

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:8000"]
ALLOWED_HOSTS=["localhost","127.0.0.1"]

# Frontend
VITE_API_URL="http://localhost:8000/api/v1"
EOF
    echo "✓ Created .env file"
else
    echo "✓ .env file exists"
fi

# Backend setup
echo ""
echo "[3/4] Setting up Backend..."
cd backend || exit

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment and installing packages..."
source venv/bin/activate
pip install -q -r requirements.txt
echo "✓ Backend ready"

# Start backend in background/new terminal
echo ""
echo "[4/4] Starting services..."
echo ""

# For macOS - use open command
if [[ "$OSTYPE" == "darwin"* ]]; then
    open -a Terminal
    sleep 1
    # Note: You'll need to manually run the backend command
    echo "Please run in the new terminal window:"
    echo "  cd backend && source venv/bin/activate && python -m uvicorn main:app --reload --port 8000"
else
    # For Linux - use xterm or gnome-terminal if available
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "cd backend && source venv/bin/activate && python -m uvicorn main:app --reload --port 8000; bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "cd backend && source venv/bin/activate && python -m uvicorn main:app --reload --port 8000" &
    else
        echo "Please manually run in another terminal:"
        echo "  cd backend && source venv/bin/activate && python -m uvicorn main:app --reload --port 8000"
    fi
fi

echo "✓ Backend starting... (http://localhost:8000)"

# Return to root and setup frontend
cd ..

if [ ! -d "node_modules" ]; then
    echo "Installing frontend packages..."
    npm install -q
fi

# Start frontend
echo ""
echo "Starting Frontend..."
npm run dev
