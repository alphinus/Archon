# 7-Agent Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARCHON AGENT SYSTEM                          │
│                     (Event-Driven)                              │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────┐
                    │ Orchestration Agent  │◄───── Master Coordinator
                    │  (orchestration)     │       - Workflow execution
                    │                      │       - Skill discovery
                    │  Skills:             │       - Task distribution
                    │  • execute_workflow  │
                    │  • discover_skills   │
                    │  • distribute_task   │
                    └──────────┬───────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
   ┌────────────────┐  ┌─────────────┐  ┌────────────────┐
   │ Testing Agent  │  │ Data Agent  │  │  DevEx Agent   │
   │   (testing)    │  │   (data)    │  │    (devex)     │
   │                │  │             │  │                │
   │ Skills:        │  │ Skills:     │  │ Skills:        │
   │ • run_tests    │  │ • generate  │  │ • dev_server   │
   │ • chaos_test   │  │ • seed_db   │  │ • inspect      │
   │ • benchmark    │  │ • scenarios │  │ • profile      │
   │ • load_test    │  │ • validate  │  │ • scaffold     │
   └────────────────┘  └─────────────┘  └────────────────┘
            │                  │                  │
            └──────────────────┼──────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
   ┌────────────────┐  ┌─────────────┐  ┌────────────────┐
   │  Docs Agent    │  │   UI Agent  │  │ Infra Agent    │
   │(documentation) │  │    (ui)     │  │(infrastructure)│
   │                │  │             │  │                │
   │ Skills:        │  │ Skills:     │  │ Skills:        │
   │ • generate     │  │ • component │  │ • docker_ops   │
   │ • update       │  │ • lint      │  │ • ci_cd        │
   │ • validate     │  │ • build     │  │ • optimize     │
   └────────────────┘  └─────────────┘  └────────────────┘
            │                  │                  │
            └──────────────────┴──────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     EVENT BUS        │◄───── Redis Pub/Sub
                    │    (Redis)           │       - Async messaging
                    │                      │       - Correlation IDs
                    │  Channels:           │       - Dead letter queue
                    │  • agent.*.request   │
                    │  • agent.*.response  │
                    │  • agent.*.status    │
                    │  • agent.broadcast   │
                    └──────────┬───────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
   ┌────────────────┐                   ┌────────────────┐
   │   PostgreSQL   │                   │     Redis      │
   │                │                   │                │
   │ • Agent state  │                   │ • Session mem  │
   │ • Workflow log │                   │ • Event queue  │
   │ • Test results │                   │ • Pub/Sub      │
   └────────────────┘                   └────────────────┘
```

---

## Agent Responsibilities

### 🎯 **Orchestration Agent** (Master Coordinator)

**Port:** -  
**Dependencies:** All other agents  
**Skills:** 3

**Purpose:** Coordinates multi-agent workflows and distributes tasks

**Example Workflow:**

```python
workflow = {
    "name": "full_testing_suite",
    "steps": [
        {"agent": "data", "skill": "generate_mock_data", "params": {"count": 100}},
        {"agent": "testing", "skill": "run_tests", "params": {"suite": "integration"}},
        {"agent": "devex", "skill": "inspect_memory", "params": {"layer": "all"}}
    ]
}
result = await orchestrator.execute_workflow(workflow)
```

---

### 🧪 **Testing Agent**

**Container:** `archon-agent-testing`  
**Dependencies:** Postgres, Redis  
**Skills:** 6

**Responsibilities:**

- Automated test execution (unit, integration, E2E)
- Chaos engineering (simulate failures)
- Performance benchmarking
- Load testing
- Regression detection
- Production validation

**Key Skills:**

- `run_tests(suites, coverage, parallel)`
- `chaos_test(scenario, duration, intensity)`
- `benchmark(component, iterations)`
- `load_test(component, target_rps, duration)`

---

### 📊 **Data & Mock Agent**

**Container:** `archon-agent-data`  
**Dependencies:** Postgres, Redis  
**Skills:** 5

**Responsibilities:**

- Generate realistic mock data
- Seed databases (Postgres, Redis, Supabase)
- Create test scenarios (happy path, error, edge case, load, chaos)
- Data validation

**Key Skills:**

- `generate_mock_data(entity_type, count)`
- `seed_database(environment, clear_existing)`
- `create_scenario(scenario_type, **params)`
- `validate_data(scope)`

---

### 🛠️ **Developer Experience (DevEx) Agent**

**Container:** `archon-agent-devex`  
**Dependencies:** Postgres, Redis  
**Skills:** 5

**Responsibilities:**

- Development server with hot reload
- Memory inspection (all layers)
- Event streaming viewer
- Performance profiling
- Project scaffolding

**Key Skills:**

- `start_dev_server(hot_reload, port, debug)`
- `inspect_memory(layer, session_id, limit)`
- `stream_events(filters, duration)`
- `profile_operation(component, params)`
- `scaffold_project(name, template_type)`

---

### 📝 **Documentation Agent**

**Container:** `archon-agent-documentation`  
**Dependencies:** Redis  
**Skills:** 3

**Responsibilities:**

- Generate documentation from code
- Update existing docs
- Validate documentation completeness
- Create API documentation

**Key Skills:**

- `generate_docs(source_path, output_format)`
- `update_docs(doc_path, changes)`
- `validate_docs(scope)`

---

### 🎨 **UI Agent**

**Container:** `archon-agent-ui`  
**Dependencies:** Redis  
**Skills:** 3

**Responsibilities:**

- Generate UI components
- Lint frontend code
- Build production assets
- Component testing

**Key Skills:**

- `generate_component(component_type, props)`
- `lint_ui(path, fix)`
- `build_ui(mode)`

---

### 🏗️ **Infrastructure Agent**

**Container:** `archon-agent-infrastructure`  
**Dependencies:** Redis, Docker Socket  
**Skills:** 3

**Responsibilities:**

- Docker container management
- CI/CD pipeline execution
- Infrastructure optimization
- Monitoring setup

**Key Skills:**

- `docker_operation(action, container)`
- `run_ci_pipeline(pipeline_config)`
- `optimize_infrastructure(target)`

---

## Communication Patterns

### 1. **Direct Skill Call** (Synchronous)

```python
# Agent A calls Agent B directly
result = await agent_a.call_skill(
    target_agent="data",
    skill="generate_mock_data",
    params={"entity_type": "users", "count": 10},
    timeout=30.0
)
```

### 2. **Event Broadcast** (Asynchronous)

```python
# Publish event to all agents
await event_bus.publish("agent.broadcast", {
    "message": "System maintenance in 5 minutes",
    "timestamp": datetime.utcnow().isoformat()
})
```

### 3. **Workflow Orchestration** (Multi-Step)

```python
# Orchestrator executes complex workflow
workflow = {
    "name": "deploy_with_tests",
    "mode": "sequential",
    "steps": [
        {"agent": "testing", "skill": "run_tests"},
        {"agent": "infrastructure", "skill": "deploy"},
        {"agent": "devex", "skill": "validate_deployment"}
    ]
}
await orchestrator.execute_workflow(workflow)
```

---

## Event Bus Channels

| Channel | Purpose | Subscribers |
|---------|---------|-------------|
| `agent.{id}.request` | Skill execution requests | Specific agent |
| `agent.{id}.response` | Skill execution results | Caller agent |
| `agent.{id}.error` | Error responses | Caller agent |
| `agent.{id}.status` | Agent status queries | Specific agent |
| `agent.broadcast` | System-wide announcements | All agents |

---

## Scaling Strategy

### Horizontal Scaling

```yaml
# Scale Testing Agent to 3 replicas
docker compose -f docker-compose.agents.yml up -d --scale agent-testing=3
```

### Resource Allocation

```yaml
agent-testing:
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 512M
      reservations:
        memory: 256M
```

---

## Health Monitoring

### Check All Agents

```bash
docker ps --filter "name=agent" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Check Specific Agent Health

```bash
# Check logs
docker logs archon-agent-testing --tail 50

# Check via health endpoint (if implemented)
docker exec archon-agent-testing python -c "import sys; sys.exit(0)"
```

### Monitor Event Bus Activity

```bash
# Monitor Redis pub/sub
docker exec -it archon-redis redis-cli MONITOR | grep "agent\."
```

---

**Last Updated:** 2025-12-04  
**Architecture Version:** 1.0  
**Status:** Infrastructure Complete, Integration Pending
