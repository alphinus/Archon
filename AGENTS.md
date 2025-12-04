# Archon Agent System - Complete Documentation

See [AGENTS.md](./AGENTS.md) for comprehensive agent documentation including:

- Architecture overview
- All 7 agent details with skills
- Quick start guide
- API reference
- Configuration
- Monitoring
- Troubleshooting

## Quick Start

```bash
# Start all agents
./scripts/start-agents.sh

# Test agents
./scripts/test-agents.sh

# View logs
docker-compose -f docker-compose.agents.yml logs -f
```

## 7 Specialized Agents

1. **Testing & Validation** - Test automation, chaos, performance
2. **DevEx** - CLI, hot reload, debugging
3. **UI/Frontend** - Component generation
4. **Documentation** - API docs, diagrams
5. **Orchestration** - Workflow coordination (master)
6. **Infrastructure** - Docker, CI/CD, monitoring
7. **Data & Mock** - Mock data, database seeding
