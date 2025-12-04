"""
Project Scaffolding for Archon

Creates new projects, agents, and skills from templates.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import shutil
import re
import json


class ProjectScaffold:
    """
    Create new Archon projects from templates.
    
    Supports:
    - New agent creation
    - New project setup
    - New skill modules
    """
    
    TEMPLATES = {
        "agent": {
            "description": "New Archon agent",
            "files": [
                ("agent.py", "agent_template.py"),
                ("__init__.py", "init_template.py"),
                ("Dockerfile", "dockerfile_template"),
                ("README.md", "readme_template.md")
            ]
        },
        "project": {
            "description": "New Archon project",
            "files": [
                ("docker-compose.yml", "compose_template.yml"),
                ("pyproject.toml", "pyproject_template.toml"),
                (".gitignore", "gitignore_template"),
                ("README.md", "project_readme_template.md")
            ]
        },
        "skill": {
            "description": "New skill module",
            "files": [
                ("skill.py", "skill_template.py"),
                ("test_skill.py", "test_skill_template.py")
            ]
        }
    }
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize scaffolder.
        
        Args:
            templates_dir: Directory containing templates (auto-detected if None)
        """
        if templates_dir:
            self.templates_dir = templates_dir
        else:
            # Auto-detect templates directory
            self.templates_dir = Path(__file__).parent / "templates"
    
    def create(
        self,
        name: str,
        template_type: str,
        target_path: Path
    ) -> Dict[str, Any]:
        """
        Create new project from template.
        
        Args:
            name: Project/agent name
            template_type: Template type (agent, project, skill)
            target_path: Where to create the project
        
        Returns:
            Result dictionary with status and details
        """
        # Validate template type
        if template_type not in self.TEMPLATES:
            return {
                "status": "error",
                "error": f"Unknown template: {template_type}"
            }
        
        # Validate name
        if not self._is_valid_name(name):
            return {
                "status": "error",
                "error": "Invalid name. Use lowercase letters, numbers, and hyphens only."
            }
        
        # Create target directory
        project_path = target_path / name
        if project_path.exists():
            return {
                "status": "error",
                "error": f"Directory already exists: {project_path}"
            }
        
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Copy and process templates
        template_info = self.TEMPLATES[template_type]
        
        for target_file, template_file in template_info["files"]:
            self._process_template(
                template_file=template_file,
                target_file=project_path / target_file,
                context={"name": name, "type": template_type}
            )
        
        # Get next steps
        next_steps = self._get_next_steps(template_type, name, project_path)
        
        return {
            "status": "success",
            "path": str(project_path),
            "next_steps": next_steps
        }
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if name is valid (lowercase, numbers, hyphens)."""
        return bool(re.match(r"^[a-z0-9-]+$", name))
    
    def _process_template(
        self,
        template_file: str,
        target_file: Path,
        context: Dict[str, str]
    ):
        """
        Process template file with variable substitution.
        
        Args:
            template_file: Template filename
            target_file: Target file path
            context: Variables for substitution
        """
        # For now, create simple templates inline
        # In production, load from templates directory
        
        templates = {
            "agent_template.py": self._get_agent_template(),
            "init_template.py": f'"""{context["name"].replace("-", " ").title()} Agent"""\n\n__version__ = "1.0.0"\n',
            "dockerfile_template": self._get_dockerfile_template(),
            "readme_template.md": self._get_readme_template(context["name"]),
        }
        
        content = templates.get(template_file, f"# {context['name']}\n")
        
        # Simple variable substitution
        for key, value in context.items():
            content = content.replace(f"{{{{{key}}}}}", value)
        
        # Write to file
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(content)
    
    def _get_agent_template(self) -> str:
        """Get agent template."""
        return '''"""
{{name}} Agent

Implementation of the {{name}} agent for Archon.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class {{name}}Agent(BaseAgent):
    """
    {{name}} Agent for Archon.
    
    Provides skills for {{name}} functionality.
    """
    
    def __init__(self, agent_id: str, event_bus: Any, memory: Any, **config):
        """Initialize {{name}} Agent."""
        self.config = config
        super().__init__(agent_id, event_bus, memory)
        logger.info(f"[{agent_id}] {{name}} Agent initialized")
    
    def _setup_skills(self) -> None:
        """Register agent skills."""
        self.register_skill("example_skill", self.example_skill)
    
    async def example_skill(self, param: str) -> Dict[str, Any]:
        """
        Example skill implementation.
        
        Args:
            param: Example parameter
        
        Returns:
            Result dictionary
        """
        logger.info(f"[{self.agent_id}] Running example_skill with param: {param}")
        
        return {
            "status": "success",
            "result": f"Processed: {param}"
        }


if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Standalone testing
        class MockEventBus:
            async def subscribe(self, topic, handler): pass
            async def publish(self, topic, event): print(f"Event: {topic}")
        
        agent = {{name}}Agent(
            agent_id="{{name}}",
            event_bus=MockEventBus(),
            memory=None
        )
        
        await agent.start()
        result = await agent.example_skill("test")
        print(f"Result: {result}")
        await agent.stop()
    
    asyncio.run(main())
'''
    
    def _get_dockerfile_template(self) -> str:
        """Get Dockerfile template."""
        return """FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY agents/{{name}} /app/agents/{{name}}
COPY agents/base_agent.py /app/agents/
COPY agents/__init__.py /app/agents/

ENV PYTHONUNBUFFERED=1
ENV AGENT_ID={{name}}

CMD ["python", "-m", "agents.{{name}}.agent"]
"""
    
    def _get_readme_template(self, name: str) -> str:
        """Get README template."""
        return f"""# {name.replace('-', ' ').title()} Agent

## Description

{name.replace('-', ' ').title()} agent for Archon AI Agent Platform.

## Skills

- `example_skill` - Example skill implementation

## Usage

```python
# Call skill via event bus
result = await event_bus.call_skill(
    '{name}',
    'example_skill',
    {{'param': 'value'}}
)
```

## Development

```bash
# Run standalone
python -m agents.{name}.agent

# Run tests
pytest tests/agents/test_{name}_agent.py
```

## Configuration

Environment variables:
- `AGENT_ID` - Agent identifier (default: {name})
- `EVENT_BUS_URL` - Redis URL for event bus
"""
    
    def _get_next_steps(
        self,
        template_type: str,
        name: str,
        path: Path
    ) -> list:
        """Get next steps after creation."""
        if template_type == "agent":
            return [
                f"cd {path}",
                "Implement agent skills in agent.py",
                "Add tests in tests/agents/test_{name}_agent.py",
                f"Run with: python -m agents.{name}.agent",
                "Add to docker-compose.yml for integration"
            ]
        elif template_type == "project":
            return [
                f"cd {path}",
                "Review and customize pyproject.toml",
                "Run: docker compose up -d",
                "Access at: http://localhost:8000"
            ]
        else:  # skill
            return [
                f"cd {path}",
                "Implement skill logic in skill.py",
                "Add tests in test_skill.py",
                "Register skill in your agent"
            ]


def create_from_template(
    name: str,
    template_type: str,
    target_path: Path
) -> Dict[str, Any]:
    """
    Create new project from template.
    
    Args:
        name: Project name
        template_type: Template type
        target_path: Target directory
    
    Returns:
        Result dictionary
    """
    scaffolder = ProjectScaffold()
    return scaffolder.create(name, template_type, target_path)
