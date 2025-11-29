#!/bin/bash
# Stop Archon - Kill all running processes

echo "🛑 Stopping Archon..."

# Kill processes on ports
echo "Stopping Backend (port 8181)..."
lsof -ti:8181 | xargs kill -9 2>/dev/null && echo "✅ Backend stopped" || echo "⚠️  Backend not running"

echo "Stopping Frontend (port 5173)..."
lsof -ti:5173 | xargs kill -9 2>/dev/null && echo "✅ Frontend stopped" || echo "⚠️  Frontend not running"

echo ""
echo "✅ Archon stopped"
