"""
CI/CD Manager for Archon

Manages GitHub Actions workflows and deployment pipelines.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)


class CICDManager:
    """
    Manages CI/CD pipelines for Archon.
    
    Features:
    - GitHub Actions workflow generation
    - Automated testing pipeline
    - Docker build and push
    - Deployment automation
    - Environment management
    
    Example:
        manager = CICDManager()
        workflow = manager.create_test_workflow()
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize CI/CD manager."""
        self.project_root = project_root or Path.cwd()
        self.workflows_dir = self.project_root / ".github" / "workflows"
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
    
    def create_test_workflow(self) -> Dict[str, Any]:
        """
        Create GitHub Actions testing workflow.
        
        Returns:
            Workflow configuration
        """
        logger.info("Creating test workflow")
        
        workflow = {
            "name": "Test",
            "on": {
                "push": {
                    "branches": ["main", "develop"]
                },
                "pull_request": {
                    "branches": ["main", "develop"]
                }
            },
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "services": {
                        "postgres": {
                            "image": "postgres:15",
                            "env": {
                                "POSTGRES_PASSWORD": "postgres",
                                "POSTGRES_DB": "archon_test"
                            },
                            "ports": ["5432:5432"],
                            "options": "--health-cmd pg_isready --health-interval 10s"
                        },
                        "redis": {
                            "image": "redis:7-alpine",
                            "ports": ["6379:6379"],
                            "options": "--health-cmd 'redis-cli ping' --health-interval 10s"
                        }
                    },
                    "steps": [
                        {
                            "name": "Checkout code",
                            "uses": "actions/checkout@v4"
                        },
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v4",
                            "with": {
                                "python-version": "3.11"
                            }
                        },
                        {
                            "name": "Install dependencies",
                            "run": "pip install -e . && pip install pytest pytest-cov"
                        },
                        {
                            "name": "Run tests",
                            "run": "pytest tests/ --cov=src --cov=agents --cov-report=xml",
                            "env": {
                                "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/archon_test",
                                "REDIS_URL": "redis://localhost:6379"
                            }
                        },
                        {
                            "name": "Upload coverage",
                            "uses": "codecov/codecov-action@v3",
                            "with": {
                                "file": "./coverage.xml"
                            }
                        }
                    ]
                }
            }
        }
        
        # Write workflow file
        workflow_path = self.workflows_dir / "test.yml"
        with open(workflow_path, 'w') as f:
            yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Test workflow created: {workflow_path}")
        
        return {
            "status": "success",
            "workflow_path": str(workflow_path),
            "workflow": workflow
        }
    
    def create_docker_build_workflow(self) -> Dict[str, Any]:
        """
        Create Docker build and push workflow.
        
        Returns:
            Workflow configuration
        """
        logger.info("Creating Docker build workflow")
        
        workflow = {
            "name": "Docker Build and Push",
            "on": {
                "push": {
                    "branches": ["main"],
                    "tags": ["v*"]
                }
            },
            "env": {
                "REGISTRY": "ghcr.io",
                "IMAGE_NAME": "${{ github.repository }}"
            },
            "jobs": {
                "build-and-push": {
                    "runs-on": "ubuntu-latest",
                    "permissions": {
                        "contents": "read",
                        "packages": "write"
                    },
                    "steps": [
                        {
                            "name": "Checkout",
                            "uses": "actions/checkout@v4"
                        },
                        {
                            "name": "Set up Docker Buildx",
                            "uses": "docker/setup-buildx-action@v3"
                        },
                        {
                            "name": "Log in to Container Registry",
                            "uses": "docker/login-action@v3",
                            "with": {
                                "registry": "${{ env.REGISTRY }}",
                                "username": "${{ github.actor }}",
                                "password": "${{ secrets.GITHUB_TOKEN }}"
                            }
                        },
                        {
                            "name": "Extract metadata",
                            "id": "meta",
                            "uses": "docker/metadata-action@v5",
                            "with": {
                                "images": "${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}"
                            }
                        },
                        {
                            "name": "Build and push",
                            "uses": "docker/build-push-action@v5",
                            "with": {
                                "context": ".",
                                "push": True,
                                "tags": "${{ steps.meta.outputs.tags }}",
                                "labels": "${{ steps.meta.outputs.labels }}",
                                "cache-from": "type=gha",
                                "cache-to": "type=gha,mode=max"
                            }
                        }
                    ]
                }
            }
        }
        
        workflow_path = self.workflows_dir / "docker-build.yml"
        with open(workflow_path, 'w') as f:
            yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Docker build workflow created: {workflow_path}")
        
        return {
            "status": "success",
            "workflow_path": str(workflow_path),
            "workflow": workflow
        }
    
    def create_deployment_workflow(
        self,
        environment: str = "production"
    ) -> Dict[str, Any]:
        """
        Create deployment workflow.
        
        Args:
            environment: Target environment
        
        Returns:
            Workflow configuration
        """
        logger.info(f"Creating deployment workflow for {environment}")
        
        workflow = {
            "name": f"Deploy to {environment.title()}",
            "on": {
                "workflow_dispatch": {},
                "push": {
                    "branches": ["main"] if environment == "production" else ["develop"]
                }
            },
            "jobs": {
                "deploy": {
                    "runs-on": "ubuntu-latest",
                    "environment": environment,
                    "steps": [
                        {
                            "name": "Checkout",
                            "uses": "actions/checkout@v4"
                        },
                        {
                            "name": "Deploy to server",
                            "run": "|\n              ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} '\n                cd /app/archon\n                docker compose pull\n                docker compose up -d\n                docker compose ps\n              '"
                        },
                        {
                            "name": "Health check",
                            "run": "|\n              sleep 10\n              curl -f ${{ secrets.APP_URL }}/health || exit 1"
                        },
                        {
                            "name": "Rollback on failure",
                            "if": "failure()",
                            "run": "|\n              ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} '\n                cd /app/archon\n                docker compose down\n                docker compose up -d --scale archon-server=0\n              '"
                        }
                    ]
                }
            }
        }
        
        workflow_path = self.workflows_dir / f"deploy-{environment}.yml"
        with open(workflow_path, 'w') as f:
            yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Deployment workflow created: {workflow_path}")
        
        return {
            "status": "success",
            "workflow_path": str(workflow_path),
            "environment": environment,
            "workflow": workflow
        }
    
    def validate_workflow(self, workflow_path: str) -> Dict[str, Any]:
        """
        Validate GitHub Actions workflow syntax.
        
        Args:
            workflow_path: Path to workflow file
        
        Returns:
            Validation results
        """
        logger.info(f"Validating workflow: {workflow_path}")
        
        path = Path(workflow_path)
        
        if not path.exists():
            return {
                "status": "error",
                "error": f"Workflow file not found: {workflow_path}"
            }
        
        try:
            with open(path) as f:
                workflow = yaml.safe_load(f)
            
            # Basic validation
            required_fields = ["name", "on", "jobs"]
            missing = [field for field in required_fields if field not in workflow]
            
            if missing:
                return {
                    "status": "invalid",
                    "missing_fields": missing
                }
            
            return {
                "status": "valid",
                "workflow_path": workflow_path,
                "jobs": list(workflow["jobs"].keys())
            }
            
        except yaml.YAMLError as e:
            return {
                "status": "error",
                "error": f"Invalid YAML: {e}"
            }
