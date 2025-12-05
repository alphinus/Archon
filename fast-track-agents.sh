#!/bin/bash

# 🚀 Fast Track: Start ALL 7 Agents Simultaneously
# This script starts all agents in parallel for maximum speed

set -e  # Exit on error

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 ARCHON 7-AGENT FAST TRACK STARTUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Start Infrastructure
echo "📦 [1/3] Starting Infrastructure (Postgres + Redis)..."
docker compose -f docker-compose.agents.yml up -d postgres redis

# Wait for infrastructure to be ready
echo "⏳ Waiting for infrastructure to be healthy (15s)..."
sleep 15

# Check infrastructure health
echo "🏥 Checking infrastructure health..."
docker ps --filter "name=archon-postgres|archon-redis" --format "table {{.Names}}\t{{.Status}}"

# Step 2: Build all agent images in parallel
echo ""
echo "🔨 [2/3] Building all agent images (parallel)..."
docker compose -f docker-compose.agents.yml build --parallel \
  agent-testing \
  agent-data \
  agent-devex \
  agent-documentation \
  agent-ui \
  agent-infrastructure \
  agent-orchestration

# Step 3: Start ALL agents simultaneously
echo ""
echo "🚀 [3/3] Starting ALL 7 AGENTS simultaneously..."
docker compose -f docker-compose.agents.yml up -d \
  agent-testing \
  agent-data \
  agent-devex \
  agent-documentation \
  agent-ui \
  agent-infrastructure \
  agent-orchestration

# Wait a moment for startup
echo "⏳ Waiting for agents to initialize (10s)..."
sleep 10

# Show status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 AGENT STATUS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker ps --filter "name=agent" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 QUICK HEALTH CHECK:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Count running vs exited agents
RUNNING=$(docker ps --filter "name=agent" --filter "status=running" -q | wc -l | tr -d ' ')
EXITED=$(docker ps -a --filter "name=agent" --filter "status=exited" -q | wc -l | tr -d ' ')

echo "✅ Running: $RUNNING agents"
echo "❌ Exited:  $EXITED agents"

if [ "$EXITED" -gt 0 ]; then
    echo ""
    echo "⚠️  WARNING: Some agents have exited!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🔍 Showing errors from exited agents:"
    echo ""
    
    for agent in agent-testing agent-data agent-devex agent-documentation agent-ui agent-infrastructure agent-orchestration; do
        STATUS=$(docker ps -a --filter "name=archon-$agent" --format "{{.Status}}" 2>/dev/null)
        if [[ $STATUS == Exited* ]]; then
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "❌ $agent (EXITED)"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            docker logs archon-$agent --tail 30
            echo ""
        fi
    done
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 SUCCESS! All agents are running!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📝 Showing last 10 lines from each agent:"
    echo ""
    
    for agent in agent-testing agent-data agent-devex agent-documentation agent-ui agent-infrastructure agent-orchestration; do
        echo "──────────────────────────────────────────────────────"
        echo "✅ $agent:"
        docker logs archon-$agent --tail 10 2>&1 | tail -5
        echo ""
    done
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 NEXT STEPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "View all logs in real-time:"
echo "  docker compose -f docker-compose.agents.yml logs -f"
echo ""
echo "View specific agent:"
echo "  docker logs archon-agent-testing -f"
echo ""
echo "Restart all agents:"
echo "  docker compose -f docker-compose.agents.yml restart"
echo ""
echo "Stop all agents:"
echo "  docker compose -f docker-compose.agents.yml down"
echo ""
