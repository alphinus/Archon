#!/bin/bash
# Quick Start Script - Start Archon Backend & Frontend
# Run this after setup.sh has completed successfully

# Kill existing processes on ports 8181 and 5173
echo "🧹 Cleaning up existing processes..."
lsof -ti:8181 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
sleep 1

echo "🚀 Starting Archon..."
echo ""

# Start backend in background
echo "Starting Backend (port 8181)..."
cd python
source .venv/bin/activate
python -m uvicorn src.server.main:app --host 0.0.0.0 --port 8181 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

sleep 3

# Check if backend started
if lsof -Pi :8181 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Backend running (PID: $BACKEND_PID)"
else
    echo "❌ Backend failed to start. Check backend.log"
    exit 1
fi

# Start frontend in background
echo "Starting Frontend (port 5173)..."
cd archon-ui-main
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

sleep 5

# Check if frontend started
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Frontend running (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend failed to start. Check frontend.log"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 Archon is running!"
echo "======================================"
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8181/docs"
echo "======================================"
echo ""
echo "📋 Process IDs:"
echo "  Backend:  $BACKEND_PID"
echo "  Frontend: $FRONTEND_PID"
echo ""
echo "To stop Archon, run: ./stop.sh"
echo "Logs: backend.log, frontend.log"
echo ""
