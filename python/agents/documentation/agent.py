"""
Documentation Agent

Generates comprehensive documentation for Archon codebase.
Auto-generates API docs, architecture diagrams, and developer guides.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import ast
import logging

logger = logging.getLogger(__name__)


class DocumentationAgent(BaseAgent):
    """
    Documentation Agent for Archon.
    
    Provides skills for:
    - Auto-generating code documentation
    - Creating architecture diagrams
    - Building API reference
    - Generating developer guides
    
    Skills:
    - generate_api_docs: Generate API documentation
    - create_architecture_diagram: Create system architecture diagram
    - generate_readme: Generate README files
    
    Example:
        agent = DocumentationAgent(
            agent_id="documentation",
            event_bus=event_bus,
            memory=memory_system
        )
        await agent.start()
    """
    
    def __init__(self, agent_id: str, event_bus: Any, memory: Any, **config):
        """Initialize Documentation Agent."""
        self.config = config
        self.project_root = Path.cwd()
        
        super().__init__(agent_id, event_bus, memory)
        
        logger.info(f"[{agent_id}] Documentation Agent initialized")
    
    def _setup_skills(self) -> None:
        """Register Documentation Agent skills."""
        self.register_skill("generate_api_docs", self.generate_api_docs)
        self.register_skill("create_architecture_diagram", self.create_architecture_diagram)
        self.register_skill("generate_readme", self.generate_readme)
    
    async def generate_api_docs(
        self,
        module_path: str,
        output_format: str = "markdown"
    ) -> Dict[str, Any]:
        """
        Generate API documentation from Python module.
        
        Args:
            module_path: Path to Python module
            output_format: Output format (markdown, html)
        
        Returns:
            Documentation content
        """
        logger.info(f"[{self.agent_id}] Generating API docs for {module_path}")
        
        try:
            module_file = self.project_root / module_path
            
            if not module_file.exists():
                return {
                    "status": "error",
                    "error": f"Module not found: {module_path}"
                }
            
            # Parse AST
            tree = ast.parse(module_file.read_text())
            
            # Extract classes and functions
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "docstring": ast.get_docstring(node) or "No documentation",
                        "methods": [
                            m.name for m in node.body 
                            if isinstance(m, ast.FunctionDef)
                        ]
                    })
                elif isinstance(node, ast.FunctionDef):
                    if not any(node in cls.body for cls in ast.walk(tree) if isinstance(cls, ast.ClassDef)):
                        functions.append({
                            "name": node.name,
                            "docstring": ast.get_docstring(node) or "No documentation"
                        })
            
            # Generate markdown documentation
            docs = f"# API Documentation: {module_path}\n\n"
            
            if classes:
                docs += "## Classes\n\n"
                for cls in classes:
                    docs += f"### `{cls['name']}`\n\n"
                    docs += f"{cls['docstring']}\n\n"
                    if cls['methods']:
                        docs += "**Methods:**\n"
                        for method in cls['methods']:
                            docs += f"- `{method}()`\n"
                        docs += "\n"
            
            if functions:
                docs += "## Functions\n\n"
                for func in functions:
                    docs += f"### `{func['name']}()`\n\n"
                    docs += f"{func['docstring']}\n\n"
            
            # Save documentation
            docs_dir = self.project_root / "docs" / "api"
            docs_dir.mkdir(parents=True, exist_ok=True)
            
            doc_file = docs_dir / f"{Path(module_path).stem}.md"
            doc_file.write_text(docs)
            
            return {
                "status": "success",
                "doc_path": str(doc_file),
                "classes_count": len(classes),
                "functions_count": len(functions)
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Doc generation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def create_architecture_diagram(
        self,
        diagram_type: str = "system"
    ) -> Dict[str, Any]:
        """
        Create architecture diagram in Mermaid format.
        
        Args:
            diagram_type: Diagram type (system, agents, database)
        
        Returns:
            Diagram content
        """
        logger.info(f"[{self.agent_id}] Creating {diagram_type} architecture diagram")
        
        diagrams = {
            "system": self._create_system_diagram(),
            "agents": self._create_agents_diagram(),
            "database": self._create_database_diagram()
        }
        
        if diagram_type not in diagrams:
            return {
                "status": "error",
                "error": f"Unknown diagram type: {diagram_type}"
            }
        
        diagram = diagrams[diagram_type]
        
        # Save diagram
        diagrams_dir = self.project_root / "docs" / "diagrams"
        diagrams_dir.mkdir(parents=True, exist_ok=True)
        
        diagram_file = diagrams_dir / f"{diagram_type}.mmd"
        diagram_file.write_text(diagram)
        
        return {
            "status": "success",
            "diagram_path": str(diagram_file),
            "diagram_type": diagram_type
        }
    
    async def generate_readme(
        self,
        component: str,
        template: str = "default"
    ) -> Dict[str, Any]:
        """
        Generate README for component.
        
        Args:
            component: Component name (e.g., 'agents/testing')
            template: Template to use
        
        Returns:
            README content
        """
        logger.info(f"[{self.agent_id}] Generating README for {component}")
        
        readme = f"""# {component.title().replace('/', ' - ')}

## Overview

[Auto-generated documentation for {component}]

## Features

- Feature 1
- Feature 2
- Feature 3

## Usage

```python
# Example usage
```

## Configuration

See [configuration guide](../docs/configuration.md)

## API Reference

See [API documentation](../docs/api/{component}.md)

## Contributing

Please read [CONTRIBUTING.md](../CONTRIBUTING.md)

## License

MIT License - see [LICENSE](../LICENSE)
"""
        
        # Save README
        component_path = self.project_root / component
        component_path.mkdir(parents=True, exist_ok=True)
        
        readme_file = component_path / "README.md"
        readme_file.write_text(readme)
        
        return {
            "status": "success",
            "readme_path": str(readme_file),
            "component": component
        }
    
    def _create_system_diagram(self) -> str:
        """Create system architecture diagram."""
        return """graph TB
    Client[Client Applications]
    Server[Archon Server]
    Agents[Agent System]
    DB[(PostgreSQL)]
    Cache[(Redis)]
    
    Client -->|HTTP/WebSocket| Server
    Server --> Agents
    Server --> DB
    Server --> Cache
    Agents --> DB
    Agents --> Cache
    
    subgraph "Agent System"
        Testing[Testing Agent]
        DevEx[DevEx Agent]
        Data[Data Agent]
        Infra[Infrastructure Agent]
        Doc[Documentation Agent]
        Orch[Orchestration Agent]
        UI[UI Agent]
    end
"""
    
    def _create_agents_diagram(self) -> str:
        """Create agents communication diagram."""
        return """graph LR
    Orch[Orchestration Agent]
    Testing[Testing Agent]
    DevEx[DevEx Agent]
    Data[Data Agent]
    Infra[Infrastructure Agent]
    Doc[Documentation Agent]
    UI[UI Agent]
    
    Orch -->|Coordinates| Testing
    Orch -->|Coordinates| DevEx
    Orch -->|Coordinates| Data
    Orch -->|Coordinates| Infra
    Orch -->|Coordinates| Doc
    Orch -->|Coordinates| UI
    
    Testing -->|Uses| Data
    DevEx -->|Uses| Data
    Infra -->|Uses| DevEx
    Doc -->|Uses| DevEx
"""
    
    def _create_database_diagram(self) -> str:
        """Create database schema diagram."""
        return """erDiagram
    USERS ||--o{ SESSIONS : has
    SESSIONS ||--o{ MEMORY : contains
    SESSIONS ||--o{ EVENTS : generates
    USERS ||--o{ WORK_ORDERS : creates
    USERS ||--o{ KNOWLEDGE : contributes
    USERS ||--o{ PROJECTS : owns
    
    USERS {
        uuid id PK
        string email
        string name
        timestamp created_at
    }
    
    SESSIONS {
        uuid id PK
        uuid user_id FK
        string agent_type
        string status
        timestamp created_at
    }
    
    MEMORY {
        uuid id PK
        uuid session_id FK
        string layer
        string key
        json value
        timestamp created_at
    }
"""


if __name__ == "__main__":
    import asyncio
    from agents.base_agent import run_agent
    
    asyncio.run(run_agent(DocumentationAgent, "documentation"))
