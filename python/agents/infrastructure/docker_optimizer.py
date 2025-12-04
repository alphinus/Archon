"""
Docker Optimizer for Archon

Optimizes Docker configurations for production deployments.
Multi-stage builds, layer caching, security scanning.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import subprocess
import logging

logger = logging.getLogger(__name__)


class DockerOptimizer:
    """
    Optimizes Docker images and configurations.
    
    Features:
    - Multi-stage build optimization
    - Layer caching strategies
    - Image size reduction
    - Security scanning
    - Resource limit recommendations
    
    Example:
        optimizer = DockerOptimizer()
        result = optimizer.optimize_dockerfile(
            dockerfile_path="Dockerfile",
            target="production"
        )
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize optimizer."""
        self.project_root = project_root or Path.cwd()
    
    def optimize_dockerfile(
        self,
        dockerfile_path: str,
        target: str = "production"
    ) -> Dict[str, Any]:
        """
        Optimize Dockerfile for production.
        
        Args:
            dockerfile_path: Path to Dockerfile
            target: Build target (development, production)
        
        Returns:
            Optimization recommendations
        """
        logger.info(f"Optimizing Dockerfile: {dockerfile_path}")
        
        dockerfile = self.project_root / dockerfile_path
        
        if not dockerfile.exists():
            return {
                "status": "error",
                "error": f"Dockerfile not found: {dockerfile_path}"
            }
        
        content = dockerfile.read_text()
        
        # Analyze Dockerfile
        recommendations = []
        
        # Check for multi-stage build
        if "FROM" not in content or content.count("FROM") < 2:
            recommendations.append({
                "type": "multi_stage",
                "priority": "high",
                "message": "Use multi-stage builds to reduce image size",
                "example": "FROM python:3.11-slim AS builder\\nFROM python:3.11-slim AS runtime"
            })
        
        # Check for layer caching
        if "COPY . ." in content:
            recommendations.append({
                "type": "layer_caching",
                "priority": "medium",
                "message": "Copy dependency files before source code for better caching",
                "example": "COPY requirements.txt .\\nRUN pip install -r requirements.txt\\nCOPY . ."
            })
        
        # Check for .dockerignore
        dockerignore = self.project_root / ".dockerignore"
        if not dockerignore.exists():
            recommendations.append({
                "type": "dockerignore",
                "priority": "high",
                "message": "Create .dockerignore to exclude unnecessary files",
                "example": "__pycache__\\n*.pyc\\n.git\\n.venv"
            })
        
        # Check for security
        if "apt-get update" in content and "apt-get clean" not in content:
            recommendations.append({
                "type": "security",
                "priority": "medium",
                "message": "Clean apt cache after installation",
                "example": "RUN apt-get clean && rm -rf /var/lib/apt/lists/*"
            })
        
        return {
            "status": "success",
            "dockerfile": dockerfile_path,
            "recommendations": recommendations,
            "optimization_score": self._calculate_score(recommendations)
        }
    
    def analyze_image_size(self, image_name: str) -> Dict[str, Any]:
        """
        Analyze Docker image size and layers.
        
        Args:
            image_name: Docker image name
        
        Returns:
            Size analysis
        """
        logger.info(f"Analyzing image size: {image_name}")
        
        try:
            # Get image size
            result = subprocess.run(
                ["docker", "images", image_name, "--format", "{{.Size}}"],
                capture_output=True,
                text=True
            )
            
            size = result.stdout.strip()
            
            # Get layer information
            result = subprocess.run(
                ["docker", "history", image_name, "--no-trunc"],
                capture_output=True,
                text=True
            )
            
            layers = result.stdout.strip().split("\n")
            
            return {
                "status": "success",
                "image": image_name,
                "size": size,
                "layer_count": len(layers),
                "layers": layers[:10]  # First 10 layers
            }
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def scan_security(self, image_name: str) -> Dict[str, Any]:
        """
        Scan Docker image for security vulnerabilities.
        
        Args:
            image_name: Docker image name
        
        Returns:
            Security scan results
        """
        logger.info(f"Scanning image security: {image_name}")
        
        try:
            # Use trivy for security scanning (if available)
            result = subprocess.run(
                ["trivy", "image", "--format", "json", image_name],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                import json
                scan_results = json.loads(result.stdout)
                
                return {
                    "status": "success",
                    "image": image_name,
                    "vulnerabilities": scan_results
                }
            else:
                return {
                    "status": "warning",
                    "message": "Trivy not available, install for security scanning"
                }
                
        except FileNotFoundError:
            return {
                "status": "warning",
                "message": "Trivy not installed. Install with: brew install trivy"
            }
        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def recommend_resource_limits(
        self,
        service_name: str,
        service_type: str = "api"
    ) -> Dict[str, Any]:
        """
        Recommend resource limits for Docker service.
        
        Args:
            service_name: Service name
            service_type: Service type (api, worker, db, cache)
        
        Returns:
            Resource recommendations
        """
        # Predefined recommendations based on service type
        recommendations = {
            "api": {
                "cpus": "1.0",
                "memory": "512M",
                "memory_reservation": "256M"
            },
            "worker": {
                "cpus": "2.0",
                "memory": "1G",
                "memory_reservation": "512M"
            },
            "db": {
                "cpus": "2.0",
                "memory": "2G",
                "memory_reservation": "1G"
            },
            "cache": {
                "cpus": "0.5",
                "memory": "256M",
                "memory_reservation": "128M"
            }
        }
        
        limits = recommendations.get(service_type, recommendations["api"])
        
        return {
            "service": service_name,
            "type": service_type,
            "recommendations": limits,
            "compose_config": {
                "deploy": {
                    "resources": {
                        "limits": {
                            "cpus": limits["cpus"],
                            "memory": limits["memory"]
                        },
                        "reservations": {
                            "memory": limits["memory_reservation"]
                        }
                    }
                }
            }
        }
    
    def _calculate_score(self, recommendations: List[Dict[str, Any]]) -> int:
        """Calculate optimization score (0-100)."""
        if not recommendations:
            return 100
        
        # Deduct points based on priority
        points_deducted = 0
        for rec in recommendations:
            if rec["priority"] == "high":
                points_deducted += 15
            elif rec["priority"] == "medium":
                points_deducted += 10
            else:
                points_deducted += 5
        
        return max(0, 100 - points_deducted)
