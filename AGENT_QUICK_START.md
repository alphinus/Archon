# 🚀 Quick Start: 7-Agent Integration

**What:** Get all 7 Archon agents running and communicating  
**Time:** ~2-3 hours for Phase 1  
**Prerequisites:** Docker Desktop, basic terminal knowledge

---

## ⚡ TL;DR - Get Started NOW

```bash
# 1. Navigate to Archon directory
cd "/Users/mg1/AI Umgebung/AI Empire HQ/Apps/Archon"

# 2. Start infrastructure
docker compose -f docker-compose.agents.yml up -d postgres redis

# 3. Wait for services to be ready (10 seconds)
sleep 10

# 4. Start first agent (Testing Agent)
docker compose -f docker-compose.agents.yml up agent-testing

# Expected: See "[testing] Agent started and listening for events"
```

---

## 📋 Step-by-Step Instructions

### Step 1: Verify Prerequisites

**Check Docker is running:**

```bash
docker ps
# Should show running containers or empty list (not an error)
```

**Check you're in correct directory:**

```bash
pwd
# Should output: /Users/mg1/AI Umgebung/AI Empire HQ/Apps/Archon
```

### Step 2: Start Infrastructure Services

**Start PostgreSQL and Redis:**

```bash
docker compose -f docker-compose.agents.yml up -d postgres redis
```

**Verify they're healthy:**

```bash
docker ps --filter "name=archon-postgres|archon-redis"
# Both should show "healthy" status after ~10 seconds
```

**Check logs (optional):**

```bash
docker logs archon-postgres --tail 20
docker logs archon-redis --tail 20
# No errors = good!
```

### Step 3: Start Testing Agent (Simplest)

**Why Testing Agent first?**

- Fewest dependencies
- Simplest codebase
- Good baseline for debugging

**Start it:**

```bash
docker compose -f docker-compose.agents.yml up agent-testing
# Runs in foreground so you see logs immediately
```

**Expected Output:**

```
archon-agent-testing  | INFO:root:Connecting to Event Bus at redis://redis:6379
archon-agent-testing  | INFO:root:[testing] Agent initialized with 6 skills
archon-agent-testing  | INFO:root:[testing] Agent started and listening for events
archon-agent-testing  | INFO:root:[testing] Successfully published status: started
archon-agent-testing  | INFO:root:Agent testing running. Press Ctrl+C to stop.
```

**If you see errors:**

- See [Troubleshooting](#troubleshooting) below
- Check `AGENT_INTEGRATION_PLAN.md` Task 1.3 (Fix Import Errors)

### Step 4: Test Agent Communication

**Open new terminal, send test event via Redis:**

```bash
docker exec -it archon-redis redis-cli

# In Redis CLI:
PUBLISH "agent.testing.status" '{"correlation_id": "test-123"}'
# Should return (integer) 1 (one subscriber received it)

# Exit Redis CLI:
exit
```

**Check Testing Agent logs:**

- You should see it received the status query
- Should see it published a response

### Step 5: Start Data Agent

**In a new terminal:**

```bash
cd "/Users/mg1/AI Umgebung/AI Empire HQ/Apps/Archon"
docker compose -f docker-compose.agents.yml up agent-data
```

**Expected Output:**

```
[data] Agent initialized with 5 skills
[data] Agent started and listening for events
```

### Step 6: Start Remaining Agents

**Start one by one, checking logs:**

```bash
# DevEx Agent
docker compose -f docker-compose.agents.yml up -d agent-devex
docker logs archon-agent-devex --tail 30

# Documentation Agent
docker compose -f docker-compose.agents.yml up -d agent-documentation
docker logs archon-agent-documentation --tail 30

# UI Agent
docker compose -f docker-compose.agents.yml up -d agent-ui
docker logs archon-agent-ui --tail 30

# Infrastructure Agent
docker compose -f docker-compose.agents.yml up -d agent-infrastructure
docker logs archon-agent-infrastructure --tail 30

# Orchestration Agent (start LAST - depends on all others)
docker compose -f docker-compose.agents.yml up -d agent-orchestration
docker logs archon-agent-orchestration --tail 30
```

### Step 7: Verify All Agents Running

**Check status:**

```bash
docker ps --filter "name=agent" --format "table {{.Names}}\t{{.Status}}"
```

**Expected output:**

```
NAMES                           STATUS
archon-agent-orchestration      Up X minutes
archon-agent-infrastructure     Up X minutes
archon-agent-ui                 Up X minutes
archon-agent-documentation      Up X minutes
archon-agent-devex              Up X minutes
archon-agent-data               Up X minutes
archon-agent-testing            Up X minutes
```

---

## 🐛 Troubleshooting

### Problem: "Cannot connect to Docker daemon"

**Solution:**

```bash
# Start Docker Desktop application
open -a Docker

# Wait 30 seconds, then retry
```

### Problem: Import error `ModuleNotFoundError: No module named 'src.events.bus'`

**Solution:**

```bash
# Check if EventBus exists
ls -la python/src/events/bus.py

# If missing, check current directory structure
find python -name "bus.py"
```

**If file exists but import fails:**

- Check `PYTHONPATH` is set correctly in docker-compose.agents.yml
- Verify `/app` is the working directory in container

### Problem: Agent exits immediately with "Connection refused"

**Cause:** Redis not ready yet

**Solution:**

```bash
# Check Redis is actually running
docker ps --filter "name=redis"

# Check Redis health
docker exec archon-redis redis-cli ping
# Should return: PONG

# If Redis not healthy, restart it
docker compose -f docker-compose.agents.yml restart redis
sleep 10
```

### Problem: Agent starts but no skills registered

**Check logs for skill registration:**

```bash
docker logs archon-agent-testing | grep "skills"
# Should see: "Agent initialized with X skills"
```

**If 0 skills:**

- Agent's `_setup_skills()` method not called
- Check agent inherits from BaseAgent correctly
- View agent source code and verify skill registration

---

## ✅ Success Criteria

**Phase 1 is COMPLETE when:**

- ✅ All 7 agents show "Up" status
- ✅ No errors in any agent logs
- ✅ Each agent logs "Agent started and listening for events"
- ✅ Skill count > 0 for each agent
- ✅ Redis shows 7+ subscribers (one per agent)

**Check Redis subscribers:**

```bash
docker exec archon-redis redis-cli PUBSUB NUMPAT
# Should return > 0 (agents subscribed to patterns)
```

---

## 🎯 What's Next?

**After Phase 1 completes:**

1. **Create integration tests** (see `AGENT_INTEGRATION_PLAN.md` Phase 2)
2. **Test inter-agent communication**
3. **Execute first end-to-end workflow**

**First Integration Test:**

```bash
# Use Orchestration Agent to query Testing Agent
docker exec archon-redis redis-cli PUBLISH \
  "agent.orchestration.request" \
  '{"correlation_id":"test-001","skill":"discover_skills","params":{"agent_filter":"testing"}}'

# Check orchestration agent logs for response
docker logs archon-agent-orchestration --tail 50
```

---

## 📚 Additional Resources

- **[AGENT_INTEGRATION_PLAN.md](AGENT_INTEGRATION_PLAN.md)** - Detailed 3-phase integration plan
- **[AI_TASKS.md](AI_TASKS.md)** - Current sprint tasks and progress
- **[python/agents/base_agent.py](python/agents/base_agent.py)** - BaseAgent source code
- **[docker-compose.agents.yml](docker-compose.agents.yml)** - Agent Docker configuration

---

**Last Updated:** 2025-12-04
**Estimated Time to Complete Phase 1:** 1-3 hours (depending on issues encountered)
