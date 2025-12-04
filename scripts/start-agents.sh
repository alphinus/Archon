#!/bin/bash

# Archon Agent System Startup Script
# Launches all 7 specialized agents in correct order

set -e

echo "🚀 Starting Archon Agent System..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Start core infrastructure
echo -e "${BLUE}Step 1/4: Starting core infrastructure (PostgreSQL, Redis)...${NC}"
docker-compose -f docker-compose.agents.yml up -d postgres redis

# Wait for databases to be healthy
echo -e "${YELLOW}Waiting for databases to become healthy...${NC}"
sleep 5

# Step 2: Start data agent (needed by others)
echo -e "${BLUE}Step 2/4: Starting Data & Mock Agent...${NC}"
docker-compose -f docker-compose.agents.yml up -d agent-data
sleep 3

# Step 3: Start worker agents
echo -e "${BLUE}Step 3/4: Starting worker agents...${NC}"
docker-compose -f docker-compose.agents.yml up -d \
  agent-testing \
  agent-devex \
  agent-ui \
  agent-documentation \
  agent-infrastructure
sleep 3

# Step 4: Start orchestration agent (master coordinator)
echo -e "${BLUE}Step 4/4: Starting Orchestration Agent (Master)...${NC}"
docker-compose -f docker-compose.agents.yml up -d agent-orchestration

echo ""
echo -e "${GREEN}✅ All agents started successfully!${NC}"
echo ""
echo "Agent Status:"
docker-compose -f docker-compose.agents.yml ps

echo ""
echo "📊 To view logs:"
echo "  All agents:           docker-compose -f docker-compose.agents.yml logs -f"
echo "  Specific agent:       docker-compose -f docker-compose.agents.yml logs -f agent-testing"
echo ""
echo "🛑 To stop all agents:"
echo "  docker-compose -f docker-compose.agents.yml down"
echo ""
echo "🔍 To check agent health:"
echo "  docker-compose -f docker-compose.agents.yml ps"
echo ""
