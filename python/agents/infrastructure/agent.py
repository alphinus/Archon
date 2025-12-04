"""
Infrastructure Agent

Coordinates Docker optimization, CI/CD, deployment, and monitoring.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent
from agents.infrastructure.docker_optimizer import DockerOptimizer
from agents.infrastructure.ci_cd_manager import CICDManager
from agents.infrastructure.monitoring_setup import MonitoringSetup
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class InfrastructureAgent(BaseAgent):
    """
    Infrastructure Agent for Archon.
    
    Provides skills for:
    - Docker optimization
    - CI/CD pipeline management
    - Deployment automation
    - Monitoring setup
    
    Skills:
    - optimize_docker: Optimize Dockerfile
    - create_ci_pipeline: Create CI/CD workflow
    - setup_monitoring: Configure monitoring stack
    - deploy: Deploy to environment
    
    Example:
        agent = InfrastructureAgent(
            agent_id="infrastructure",
            event_bus=event_bus,
            memory=memory_system
        )
        await agent.start()
    """
    
    def __init__(self, agent_id: str, event_bus: Any, memory: Any, **config):
        """Initialize Infrastructure Agent."""
        self.config = config
        self.docker_optimizer = DockerOptimizer()
        self.cicd_manager = CICDManager()
        self.monitoring_setup = MonitoringSetup()
        
        super().__init__(agent_id, event_bus, memory)
        
        logger.info(f"[{agent_id}] Infrastructure Agent initialized")
    
    def _setup_skills(self) -> None:
        """Register Infrastructure Agent skills."""
        self.register_skill("optimize_docker", self.optimize_docker)
        self.register_skill("create_ci_pipeline", self.create_ci_pipeline)
        self.register_skill("setup_monitoring", self.setup_monitoring)
        self.register_skill("analyze_image", self.analyze_image)
    
    async def optimize_docker(
        self,
        dockerfile_path: str = "Dockerfile",
        target: str = "production"
    ) -> Dict[str, Any]:
        """
        Optimize Dockerfile.
        
        Args:
            dockerfile_path: Path to Dockerfile
            target: Build target
        
        Returns:
            Optimization recommendations
        """
        logger.info(f"[{self.agent_id}] Optimizing Dockerfile: {dockerfile_path}")
        
        try:
            result = self.docker_optimizer.optimize_dockerfile(
                dockerfile_path=dockerfile_path,
                target=target
            )
            
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Docker optimization failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def create_ci_pipeline(
        self,
        pipeline_type: str = "test",
        environment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create CI/CD pipeline.
        
        Args:
            pipeline_type: Pipeline type (test, docker-build, deploy)
            environment: Deployment environment (for deploy pipelines)
        
        Returns:
            Pipeline configuration
        """
        logger.info(f"[{self.agent_id}] Creating {pipeline_type} pipeline")
        
        try:
            if pipeline_type == "test":
                result = self.cicd_manager.create_test_workflow()
            elif pipeline_type == "docker-build":
                result = self.cicd_manager.create_docker_build_workflow()
            elif pipeline_type == "deploy":
                if not environment:
                    return {
                        "status": "error",
                        "error": "Environment required for deploy pipeline"
                    }
                result = self.cicd_manager.create_deployment_workflow(environment)
            else:
                return {
                    "status": "error",
                    "error": f"Unknown pipeline type: {pipeline_type}"
                }
            
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Pipeline creation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def setup_monitoring(
        self,
        components: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Setup monitoring stack.
        
        Args:
            components: Components to setup (prometheus, grafana, alerts, all)
        
        Returns:
            Setup results
        """
        logger.info(f"[{self.agent_id}] Setting up monitoring")
        
        components = components or ["all"]
        results = {}
        
        try:
            if "all" in components or "prometheus" in components:
                results["prometheus"] = self.monitoring_setup.create_prometheus_config()
            
            if "all" in components or "grafana" in components:
                results["grafana"] = self.monitoring_setup.create_grafana_dashboard()
            
            if "all" in components or "alerts" in components:
                results["alerts"] = self.monitoring_setup.create_alert_rules()
            
            if "all" in components:
                results["compose"] = self.monitoring_setup.create_docker_compose_monitoring()
            
            return {
                "status": "success",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Monitoring setup failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def analyze_image(
        self,
        image_name: str,
        scan_security: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze Docker image.
        
        Args:
            image_name: Docker image name
            scan_security: Run security scan
        
        Returns:
            Analysis results
        """
        logger.info(f"[{self.agent_id}] Analyzing image: {image_name}")
        
        try:
            size_analysis = self.docker_optimizer.analyze_image_size(image_name)
            
            results = {
                "size_analysis": size_analysis
            }
            
            if scan_security:
                security_scan = self.docker_optimizer.scan_security(image_name)
                results["security_scan"] = security_scan
            
            return {
                "status": "success",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Image analysis failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }


if __name__ == "__main__":
    import asyncio
    from agents.base_agent import run_agent
    
    asyncio.run(run_agent(InfrastructureAgent, "infrastructure"))
