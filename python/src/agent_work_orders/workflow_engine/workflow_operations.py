"""Workflow Operations

Refactored to use the Agent Abstraction Layer (AAL).
Each function constructs an AgentRequest and uses the AgentService.
"""

import time

from aal.models import AgentRequest
from aal.service import AgentService
from ..command_loader.claude_command_loader import ClaudeCommandLoader
from ..models import StepExecutionResult, WorkflowStep, WorkflowExecutionError
from ..utils.structured_logger import get_logger
from .agent_names import (
    BRANCH_CREATOR,
    COMMITTER,
    IMPLEMENTOR,
    PLANNER,
    PR_CREATOR,
    REVIEWER,
)

logger = get_logger(__name__)


async def run_create_branch_step(
    agent_service: AgentService,
    command_loader: ClaudeCommandLoader,
    work_order_id: str,
    working_dir: str,  # Note: working_dir is currently unused for AAL-only calls
    context: dict,
) -> StepExecutionResult:
    """Creates a git branch based on user request using the AAL."""
    start_time = time.time()
    try:
        prompt_template = command_loader.load_command_text("create-branch")
        user_request = context.get("user_request", "")
        prompt = prompt_template.replace("$ARGUMENTS", user_request)

        request = AgentRequest(
            prompt=prompt,
            preferred_provider="anthropic"  # Explicitly use Claude for now
        )
        response = await agent_service.execute_request(request)
        duration = time.time() - start_time

        if response.error:
            raise WorkflowExecutionError(response.error)

        branch_name = response.content.strip()
        return StepExecutionResult(
            step=WorkflowStep.CREATE_BRANCH,
            agent_name=BRANCH_CREATOR,
            success=True,
            output=branch_name,
            duration_seconds=duration,
            session_id=response.session_id if hasattr(response, 'session_id') else None,
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error("create_branch_step_error", error=str(e), exc_info=True)
        return StepExecutionResult(
            step=WorkflowStep.CREATE_BRANCH,
            agent_name=BRANCH_CREATOR,
            success=False,
            error_message=str(e),
            duration_seconds=duration,
        )


async def run_planning_step(
    agent_service: AgentService,
    command_loader: ClaudeCommandLoader,
    work_order_id: str,
    working_dir: str,
    context: dict,
) -> StepExecutionResult:
    """Creates a PRP plan based on user request using the AAL."""
    start_time = time.time()
    try:
        prompt_template = command_loader.load_command_text("planning")
        user_request = context.get("user_request", "")
        github_issue = context.get("github_issue_number") or ""
        
        prompt = prompt_template.replace("$1", user_request).replace("$2", github_issue)

        request = AgentRequest(prompt=prompt, preferred_provider="anthropic")
        response = await agent_service.execute_request(request)
        duration = time.time() - start_time

        if response.error:
            raise WorkflowExecutionError(response.error)

        plan_file_content = response.content.strip()
        return StepExecutionResult(
            step=WorkflowStep.PLANNING,
            agent_name=PLANNER,
            success=True,
            output=plan_file_content,
            duration_seconds=duration,
            session_id=response.session_id if hasattr(response, 'session_id') else None,
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error("planning_step_error", error=str(e), exc_info=True)
        return StepExecutionResult(
            step=WorkflowStep.PLANNING,
            agent_name=PLANNER,
            success=False,
            error_message=str(e),
            duration_seconds=duration,
        )


async def run_execute_step(
    agent_service: AgentService,
    command_loader: ClaudeCommandLoader,
    work_order_id: str,
    working_dir: str,
    context: dict,
) -> StepExecutionResult:
    """Implements the PRP plan using the AAL."""
    start_time = time.time()
    try:
        plan_content = context.get("planning", "")
        if not plan_content:
            raise ValueError("No plan content found in context.")

        prompt_template = command_loader.load_command_text("execute")
        prompt = prompt_template.replace("$ARGUMENTS", plan_content)

        request = AgentRequest(prompt=prompt, preferred_provider="anthropic")
        response = await agent_service.execute_request(request)
        duration = time.time() - start_time

        if response.error:
            raise WorkflowExecutionError(response.error)
        
        summary = response.content or "Implementation completed."
        return StepExecutionResult(
            step=WorkflowStep.EXECUTE,
            agent_name=IMPLEMENTOR,
            success=True,
            output=summary,
            duration_seconds=duration,
            session_id=response.session_id if hasattr(response, 'session_id') else None,
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error("execute_step_error", error=str(e), exc_info=True)
        return StepExecutionResult(
            step=WorkflowStep.EXECUTE,
            agent_name=IMPLEMENTOR,
            success=False,
            error_message=str(e),
            duration_seconds=duration,
        )


async def run_commit_step(
    agent_service: AgentService,
    command_loader: ClaudeCommandLoader,
    work_order_id: str,
    working_dir: str,
    context: dict,
) -> StepExecutionResult:
    """Commits changes and pushes to remote using the AAL."""
    start_time = time.time()
    try:
        # Commit command doesn't need args in the prompt, it usually acts on current changes.
        # However, we can pass context information if the agent needs it to formulate the commit message.
        prompt_template = command_loader.load_command_text("commit")
        # Example: Pass previous step outputs or user request for context
        plan_summary = context.get("planning", "")
        execute_summary = context.get("execute", "")
        
        prompt = prompt_template.replace("$1", plan_summary).replace("$2", execute_summary)

        request = AgentRequest(prompt=prompt, preferred_provider="anthropic")
        response = await agent_service.execute_request(request)
        duration = time.time() - start_time

        if response.error:
            raise WorkflowExecutionError(response.error)

        commit_info = response.content.strip()
        return StepExecutionResult(
            step=WorkflowStep.COMMIT,
            agent_name=COMMITTER,
            success=True,
            output=commit_info,
            duration_seconds=duration,
            session_id=response.session_id if hasattr(response, 'session_id') else None,
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error("commit_step_error", error=str(e), exc_info=True)
        return StepExecutionResult(
            step=WorkflowStep.COMMIT,
            agent_name=COMMITTER,
            success=False,
            error_message=str(e),
            duration_seconds=duration,
        )


async def run_create_pr_step(
    agent_service: AgentService,
    command_loader: ClaudeCommandLoader,
    work_order_id: str,
    working_dir: str,
    context: dict,
) -> StepExecutionResult:
    """Creates a GitHub pull request using the AAL."""
    start_time = time.time()
    try:
        branch_name = context.get("create-branch", "")
        if not branch_name:
            raise ValueError("No branch name found in context.")

        prompt_template = command_loader.load_command_text("create-pr")
        # Pass branch name and planning output to agent for PR description
        plan_content = context.get("planning", "")
        prompt = prompt_template.replace("$1", branch_name).replace("$2", plan_content)

        request = AgentRequest(prompt=prompt, preferred_provider="anthropic")
        response = await agent_service.execute_request(request)
        duration = time.time() - start_time

        if response.error:
            raise WorkflowExecutionError(response.error)

        pr_url = response.content.strip()
        return StepExecutionResult(
            step=WorkflowStep.CREATE_PR,
            agent_name=PR_CREATOR,
            success=True,
            output=pr_url,
            duration_seconds=duration,
            session_id=response.session_id if hasattr(response, 'session_id') else None,
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error("create_pr_step_error", error=str(e), exc_info=True)
        return StepExecutionResult(
            step=WorkflowStep.CREATE_PR,
            agent_name=PR_CREATOR,
            success=False,
            error_message=str(e),
            duration_seconds=duration,
        )


async def run_review_step(
    agent_service: AgentService,
    command_loader: ClaudeCommandLoader,
    work_order_id: str,
    working_dir: str,
    context: dict,
) -> StepExecutionResult:
    """Reviews implementation against PRP specification using the AAL."""
    start_time = time.time()
    try:
        plan_content = context.get("planning", "")
        if not plan_content:
            raise ValueError("No plan content found in context.")

        prompt_template = command_loader.load_command_text("prp-review")
        prompt = prompt_template.replace("$ARGUMENTS", plan_content)

        request = AgentRequest(prompt=prompt, preferred_provider="anthropic")
        response = await agent_service.execute_request(request)
        duration = time.time() - start_time

        if response.error:
            raise WorkflowExecutionError(response.error)

        review_output = response.content.strip()
        return StepExecutionResult(
            step=WorkflowStep.REVIEW,
            agent_name=REVIEWER,
            success=True,
            output=review_output,
            duration_seconds=duration,
            session_id=response.session_id if hasattr(response, 'session_id') else None,
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error("review_step_error", error=str(e), exc_info=True)
        return StepExecutionResult(
            step=WorkflowStep.REVIEW,
            agent_name=REVIEWER,
            success=False,
            error_message=str(e),
            duration_seconds=duration,
        )
