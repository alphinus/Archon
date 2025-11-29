#!/bin/bash
# Archon Setup Script - Automated Environment Setup
# This script sets up everything needed to run Archon locally

set -e  # Exit on error

echo "🚀 Archon Setup - Automated Installation"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Check Python
echo "1️⃣  Checking Python..."
if ! command_exists python3; then
    error "Python 3 not found! Please install Python 3.8+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
success "Python $PYTHON_VERSION found"
echo ""

# 2. Check/Install Redis
echo "2️⃣  Checking Redis..."
if ! command_exists redis-server; then
    warning "Redis not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew install redis
            success "Redis installed via Homebrew"
        else
            error "Homebrew not found. Please install Redis manually: https://redis.io/download"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo apt-get update && sudo apt-get install -y redis-server
        success "Redis installed via apt"
    else
        error "Unsupported OS. Please install Redis manually: https://redis.io/download"
        exit 1
    fi
else
    success "Redis already installed"
fi

# Start Redis if not running
if ! redis-cli ping >/dev/null 2>&1; then
    warning "Starting Redis..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start redis
    else
        sudo systemctl start redis-server
    fi
    sleep 2
    if redis-cli ping >/dev/null 2>&1; then
        success "Redis started successfully"
    else
        error "Failed to start Redis"
        exit 1
    fi
else
    success "Redis is running"
fi
echo ""

# 3. Setup .env file
echo "3️⃣  Setting up environment variables..."
if [ ! -f .env ]; then
    warning ".env not found. Creating from .env.example..."
    cp .env.example .env
    success ".env created"
    echo ""
    warning "⚠️  ACTION REQUIRED:"
    echo "Please edit .env and add your credentials:"
    echo "  - SUPABASE_URL"
    echo "  - SUPABASE_SERVICE_KEY"
    echo ""
    read -p "Press Enter after you've updated .env (or Ctrl+C to exit and do it later)..."
else
    success ".env already exists"
fi
echo ""

# 4. Check .env has required values
echo "4️⃣  Validating environment..."
if ! grep -q "^SUPABASE_URL=.\+" .env; then
    error "SUPABASE_URL not set in .env"
    echo "Please set SUPABASE_URL in .env and run this script again"
    exit 1
fi
if ! grep -q "^SUPABASE_SERVICE_KEY=.\+" .env; then
    error "SUPABASE_SERVICE_KEY not set in .env"
    echo "Please set SUPABASE_SERVICE_KEY in .env and run this script again"
    exit 1
fi
success "Environment variables validated"
echo ""

# 5. Setup Python virtual environment
echo "5️⃣  Setting up Python environment..."
cd python
if [ ! -d ".venv" ]; then
    warning "Creating virtual environment..."
    python3 -m venv .venv
    success "Virtual environment created"
fi

# Activate virtual environment
source .venv/bin/activate
success "Virtual environment activated"

# Install dependencies
warning "Installing Python dependencies (this may take a few minutes)..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1 || pip install uv && uv pip install -r requirements.txt
success "Dependencies installed"
cd ..
echo ""

# 6. Check Database Tables (optional - will fail gracefully)
echo "6️⃣  Checking database setup..."
warning "Note: You may need to run Supabase migrations manually"
echo "Migration files are in: ./migration/"
echo ""

# 7. Seed test data (optional)
echo "7️⃣  Seeding test data..."
read -p "Do you want to seed the database with test data? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd python
    source .venv/bin/activate
    python seed_test_database.py || warning "Seeding failed (this is optional)"
    cd ..
    success "Test data seeded (if successful)"
else
    warning "Skipping test data seeding"
fi
echo ""

# 8. Setup Frontend
echo "8️⃣  Setting up Frontend..."
if [ -d "archon-ui-main" ]; then
    cd archon-ui-main
    if [ ! -d "node_modules" ]; then
        warning "Installing frontend dependencies..."
        npm install > /dev/null 2>&1
        success "Frontend dependencies installed"
    else
        success "Frontend dependencies already installed"
    fi
    cd ..
else
    warning "Frontend directory not found (archon-ui-main)"
fi
echo ""

# 9. Summary
echo "✅ Setup Complete!"
echo "=================="
echo ""
echo "🚀 To start Archon:"
echo ""
echo "Backend (Terminal 1):"
echo "  cd python"
echo "  source .venv/bin/activate"
echo "  python -m uvicorn src.server.main:app --host 0.0.0.0 --port 8181 --reload"
echo ""
echo "Frontend (Terminal 2):"
echo "  cd archon-ui-main"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:5173"
echo ""
echo "📚 Documentation:"
echo "  - API: http://localhost:8181/docs"
echo "  - Memory Inspector: http://localhost:5173/memory"
echo ""
