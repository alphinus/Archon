"""
Archon Multi-Agent System

This package contains 7 specialized agents that work together to provide
a complete AI agent development platform:

1. Testing & Validation Agent - Automated testing and validation
2. Developer Experience Agent - CLI tools and hot reload
3. UI/Frontend Agent - Web interface components
4. Documentation Agent - Code and architecture documentation
5. Orchestration Agent - Multi-agent workflow coordination
6. Infrastructure Agent - Deployment and monitoring
7. Data & Mock Agent - Test data generation

All agents inherit from BaseAgent and communicate via the Event Bus.
"""

from agents.base_agent import BaseAgent

__all__ = ["BaseAgent"]
