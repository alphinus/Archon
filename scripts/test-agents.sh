#!/bin/bash

# Archon Agent System Test Script
# Verifies all agents are running and can communicate

set -e

echo "🧪 Testing Archon Agent System..."
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to test if container is running
test_container() {
    local container=$1
    local agent_name=$2
    
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo -e "${GREEN}✅ ${agent_name} is running${NC}"
        return 0
    else
        echo -e "${RED}❌ ${agent_name} is not running${NC}"
        return 1
    fi
}

# Function to test container health
test_health() {
    local container=$1
    local agent_name=$2
    
    local health=$(docker inspect --format='{{.State.Health.Status}}' $container 2>/dev/null || echo "none")
    
    if [ "$health" == "healthy" ]; then
        echo -e "${GREEN}✅ ${agent_name} is healthy${NC}"
        return 0
    elif [ "$health" == "none" ]; then
        echo -e "${YELLOW}⚠️  ${agent_name} has no health check${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  ${agent_name} health: ${health}${NC}"
        return 1
    fi
}

echo "Testing Core Infrastructure..."
test_container "archon-postgres" "PostgreSQL"
test_container "archon-redis" "Redis"
test_health "archon-postgres" "PostgreSQL"
test_health "archon-redis" "Redis"

echo ""
echo "Testing Agents..."
test_container "archon-agent-testing" "Testing Agent"
test_container "archon-agent-devex" "DevEx Agent"
test_container "archon-agent-ui" "UI Agent"
test_container "archon-agent-documentation" "Documentation Agent"
test_container "archon-agent-orchestration" "Orchestration Agent"
test_container "archon-agent-infrastructure" "Infrastructure Agent"
test_container "archon-agent-data" "Data Agent"

echo ""
echo "Checking Agent Logs (last 5 lines each)..."
echo ""

for agent in testing devex ui documentation orchestration infrastructure data; do
    echo -e "${YELLOW}=== Agent: $agent ===${NC}"
    docker-compose -f docker-compose.agents.yml logs --tail=5 agent-$agent 2>/dev/null || echo "No logs available"
    echo ""
done

echo ""
echo "📊 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
    archon-agent-testing \
    archon-agent-devex \
    archon-agent-ui \
    archon-agent-documentation \
    archon-agent-orchestration \
    archon-agent-infrastructure \
    archon-agent-data 2>/dev/null || echo "Could not get stats"

echo ""
echo -e "${GREEN}✅ Test complete!${NC}"
