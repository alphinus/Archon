"""
Orchestration Agent

Coordinates multi-agent workflows and manages skill execution.
Acts as the "master" agent orchestrating tasks across the agent system.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class OrchestrationAgent(BaseAgent):
    """
    Orchestration Agent for Archon.
    
    Coordinates multi-agent workflows and task distribution.
    
    Provides skills for:
    - Multi-agent workflow execution
    - Skill discovery across agents
    - Task queue management
    - Workflow templates
    
    Skills:
    - execute_workflow: Run multi-agent workflow
    - discover_skills: Find available skills
    - distribute_task: Distribute task to best agent
    
    Example:
        agent = OrchestrationAgent(
            agent_id="orchestration",
            event_bus=event_bus,
            memory=memory_system
        )
        await agent.start()
    """
    
    def __init__(self, agent_id: str, event_bus: Any, memory: Any, **config):
        """Initialize Orchestration Agent."""
        self.config = config
        self.registered_agents = {}
        self.skill_registry = {}
        
        super().__init__(agent_id, event_bus, memory)
        
        logger.info(f"[{agent_id}] Orchestration Agent initialized")
    
    def _setup_skills(self) -> None:
        """Register Orchestration Agent skills."""
        self.register_skill("execute_workflow", self.execute_workflow)
        self.register_skill("discover_skills", self.discover_skills)
        self.register_skill("distribute_task", self.distribute_task)
        self.register_skill("register_agent", self.register_agent_skill)
    
    async def execute_workflow(
        self,
        workflow: Dict[str, Any],
        mode: str = "sequential"
    ) -> Dict[str, Any]:
        """
        Execute multi-agent workflow.
        
        Args:
            workflow: Workflow definition with steps
            mode: Execution mode (sequential, parallel)
        
        Returns:
            Workflow results
        
        Example:
            workflow = {
                "name": "production_validation",
                "steps": [
                    {"agent": "data", "skill": "seed_database", "params": {"environment": "test"}},
                    {"agent": "testing", "skill": "run_tests", "params": {"coverage": True}},
                    {"agent": "testing", "skill": "validate_production", "params": {}}
                ]
            }
            result = await agent.execute_workflow(workflow, mode="sequential")
        """
        logger.info(
            f"[{self.agent_id}] Executing workflow: {workflow.get('name')} "
            f"(mode={mode})"
        )
        
        try:
            steps = workflow.get("steps", [])
            results = []
            
            if mode == "sequential":
                # Execute steps one by one
                for i, step in enumerate(steps):
                    logger.info(f"[{self.agent_id}] Executing step {i+1}/{len(steps)}: {step}")
                    
                    result = await self._execute_step(step)
                    results.append(result)
                    
                    # Stop on error if step is critical
                    if result.get("status") == "error" and step.get("critical", True):
                        logger.error(f"[{self.agent_id}] Critical step failed, stopping workflow")
                        break
            
            elif mode == "parallel":
                # Execute all steps in parallel
                tasks = [self._execute_step(step) for step in steps]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            else:
                return {
                    "status": "error",
                    "error": f"Unknown execution mode: {mode}"
                }
            
            # Analyze results
            success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
            
            return {
                "status": "success" if success_count == len(steps) else "partial",
                "workflow_name": workflow.get("name"),
                "steps_executed": len(results),
                "steps_succeeded": success_count,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Workflow execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def discover_skills(
        self,
        agent_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Discover available skills across agents.
        
        Args:
            agent_filter: Filter by agent ID (None for all)
        
        Returns:
            Available skills
        
        Example:
            skills = await agent.discover_skills(agent_filter="testing")
            # Returns: {"testing": ["run_tests", "chaos_test", "benchmark", ...]}
        """
        logger.info(f"[{self.agent_id}] Discovering skills (filter={agent_filter})")
        
        try:
            # Query all agents for their skills
            agents = ["testing", "devex", "data", "infrastructure", "documentation", "ui"]
            
            if agent_filter:
                agents = [a for a in agents if a == agent_filter]
            
            skills_map = {}
            
            for agent in agents:
                # Request skills from agent via event bus
                response = await self.call_skill(
                    agent_id=agent,
                    skill_name="status",
                    params={},
                    timeout=5.0
                )
                
                if response.get("status") == "success":
                    skills_map[agent] = response.get("skills", [])
                else:
                    skills_map[agent] = []
            
            return {
                "status": "success",
                "skills": skills_map,
                "total_agents": len(skills_map),
                "total_skills": sum(len(s) for s in skills_map.values())
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Skill discovery failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def distribute_task(
        self,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Distribute task to best-suited agent.
        
        Args:
            task: Task definition
        
        Returns:
            Task execution result
        
        Example:
            task = {
                "type": "testing",
                "action": "run_tests",
                "params": {"suite": "memory"}
            }
            result = await agent.distribute_task(task)
        """
        logger.info(f"[{self.agent_id}] Distributing task: {task.get('type')}")
        
        try:
            # Task type to agent mapping
            agent_mapping = {
                "testing": "testing",
                "chaos": "testing",
                "performance": "testing",
                "development": "devex",
                "debugging": "devex",
                "data": "data",
                "deployment": "infrastructure",
                "monitoring": "infrastructure",
                "documentation": "documentation"
            }
            
            task_type = task.get("type")
            agent_id = agent_mapping.get(task_type)
            
            if not agent_id:
                return {
                    "status": "error",
                    "error": f"Unknown task type: {task_type}"
                }
            
            # Execute task on appropriate agent
            result = await self.call_skill(
                agent_id=agent_id,
                skill_name=task.get("action"),
                params=task.get("params", {}),
                timeout=task.get("timeout", 60.0)
            )
            
            return {
                "status": "success",
                "assigned_agent": agent_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Task distribution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def register_agent_skill(
        self,
        agent_id: str,
        skills: List[str]
    ) -> Dict[str, Any]:
        """
        Register agent and its skills.
        
        Args:
            agent_id: Agent identifier
            skills: List of skill names
        
        Returns:
            Registration confirmation
        """
        logger.info(f"[{self.agent_id}] Registering agent: {agent_id} with {len(skills)} skills")
        
        self.registered_agents[agent_id] = {
            "skills": skills,
            "registered_at": asyncio.get_event_loop().time()
        }
        
        # Update skill registry
        for skill in skills:
            if skill not in self.skill_registry:
                self.skill_registry[skill] = []
            self.skill_registry[skill].append(agent_id)
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "skills_count": len(skills)
        }
    
    async def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step."""
        agent_id = step.get("agent")
        skill_name = step.get("skill")
        params = step.get("params", {})
        timeout = step.get("timeout", 30.0)
        
        logger.debug(f"[{self.agent_id}] Executing step: {agent_id}.{skill_name}")
        
        try:
            result = await self.call_skill(
                agent_id=agent_id,
                skill_name=skill_name,
                params=params,
                timeout=timeout
            )
            
            return {
                "status": "success",
                "agent": agent_id,
                "skill": skill_name,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Step execution failed: {e}")
            return {
                "status": "error",
                "agent": agent_id,
                "skill": skill_name,
                "error": str(e)
            }


if __name__ == "__main__":
    import asyncio
    from agents.base_agent import run_agent
    
    asyncio.run(run_agent(OrchestrationAgent, "orchestration"))
