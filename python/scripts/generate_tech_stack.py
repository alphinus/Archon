#!/usr/bin/env python3
"""
Automatically generate .context/tech_stack.json from project files.
This ensures KIs always have accurate version information without manual maintenance.

Run this script during build/install to keep tech stack documentation fresh.
"""

import json
import re
from pathlib import Path
from datetime import datetime


def extract_python_version():
    """Extract Python version from pyproject.toml."""
    try:
        pyproject = Path("python/pyproject.toml").read_text()
        match = re.search(r'requires-python = ">=(\d+\.\d+)"', pyproject)
        return match.group(1) if match else "3.12"
    except FileNotFoundError:
        return "3.12"


def extract_node_react_versions():
    """Extract Node, React, TypeScript versions from package.json."""
    try:
        package_json = Path("archon-ui-main/package.json").read_text()
        pkg = json.loads(package_json)
        return {
            "node": pkg.get("engines", {}).get("node", "18+"),
            "react": pkg.get("dependencies", {}).get("react", "^18.3.1"),
            "typescript": pkg.get("devDependencies", {}).get("typescript", "^5.6.2"),
        }
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "node": "18+",
            "react": "^18.3.1",
            "typescript": "^5.6.2"
        }


def extract_docker_versions():
    """Extract Docker image versions from docker-compose.yml."""
    try:
        compose = Path("docker-compose.yml").read_text()
        python_match = re.search(r'image:.*python:(\d+\.\d+)', compose)
        return {
            "python_image": python_match.group(1) if python_match else "3.12"
        }
    except FileNotFoundError:
        return {"python_image": "3.12"}


def generate():
    """Generate .context/tech_stack.json with current project versions."""
    tech_stack = {
        "_generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "_note": "Auto-generated. Do not edit manually. Run python/scripts/generate_tech_stack.py to update.",
        "backend": {
            "python": extract_python_version(),
            "framework": "FastAPI 0.104+",
            "package_manager": "uv",
            "database": "PostgreSQL (Supabase)",
            "cache": "Redis (optional)",
            "orm": "Supabase Client (PostgreSQL)",
        },
        "frontend": {
            **extract_node_react_versions(),
            "framework": "Vite",
            "ui_library": "Radix UI",
            "styling": "Tailwind CSS",
            "query": "TanStack Query v5",
            "testing": "Vitest + React Testing Library",
        },
        "infrastructure": {
            **extract_docker_versions(),
            "container": "Docker Compose",
            "ports": {
                "frontend": 3737,
                "backend": 8181,
                "mcp": 8051,
                "agents": 8052,
                "work_orders": 8053
            }
        },
        "linting": {
            "backend": "Ruff + MyPy",
            "frontend_features": "Biome (120 char lines)",
            "frontend_legacy": "ESLint"
        }
    }

    output_path = Path(".context/tech_stack.json")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(tech_stack, indent=2) + "\n")
    print(f"✅ Generated {output_path}")


if __name__ == "__main__":
    generate()
