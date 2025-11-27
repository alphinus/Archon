"""Repository Configuration Repository

Provides database operations for managing configured GitHub repositories.
Stores repository metadata, verification status, and per-repository preferences.

File-backed fallback:
- When STATE_STORAGE_TYPE=file (or SUPABASE credentials are missing), repositories
  are stored in a local JSON file to avoid Supabase migrations during local dev.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from supabase import Client, create_client

from ..config import config
from ..models import ConfiguredRepository, SandboxType, WorkflowStep
from ..utils.structured_logger import get_logger

logger = get_logger(__name__)


def get_supabase_client() -> Client:
    """Get a Supabase client instance for agent work orders.

    Returns:
        Supabase client instance

    Raises:
        ValueError: If environment variables are not set
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables"
        )

    return create_client(url, key)


class RepositoryConfigRepository:
    """Repository for managing configured repositories in Supabase or file storage"""

    def __init__(self) -> None:
        self.table_name: str = "archon_configured_repositories"
        self._logger = logger.bind(table=self.table_name)

        # File-backed mode for local dev or when Supabase creds missing
        self.file_mode = config.STATE_STORAGE_TYPE.lower() == "file" or not (
            os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY")
        )

        if self.file_mode:
            state_dir = Path(config.FILE_STATE_DIRECTORY or "/tmp/agent-work-orders")
            state_dir.mkdir(parents=True, exist_ok=True)
            self.file_path = state_dir / "configured_repositories.json"
            if not self.file_path.exists():
                self.file_path.write_text("[]", encoding="utf-8")
            self._logger.info(
                "repository_config_repository_initialized",
                storage="file",
                path=str(self.file_path),
            )
            return

        self.client: Client = get_supabase_client()
        self._logger.info("repository_config_repository_initialized", storage="supabase")

    # ---------------------------------------------------------------------
    # File-backed helpers
    # ---------------------------------------------------------------------
    def _load_file_repos(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_file_repos(self, repos: list[dict[str, Any]]) -> None:
        self.file_path.write_text(json.dumps(repos, ensure_ascii=False, indent=2), encoding="utf-8")

    def _file_row_to_model(self, row: dict[str, Any]) -> ConfiguredRepository:
        return ConfiguredRepository(
            id=row["id"],
            repository_url=row["repository_url"],
            display_name=row.get("display_name"),
            owner=row.get("owner"),
            default_branch=row.get("default_branch"),
            is_verified=row.get("is_verified", False),
            last_verified_at=row.get("last_verified_at"),
            default_sandbox_type=SandboxType(row.get("default_sandbox_type", "git_worktree")),
            default_commands=[WorkflowStep(cmd) for cmd in row.get("default_commands", [])]
            if row.get("default_commands")
            else list(WorkflowStep),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    # ---------------------------------------------------------------------
    # Supabase helper
    # ---------------------------------------------------------------------
    def _row_to_model(self, row: dict[str, Any]) -> ConfiguredRepository:
        repository_id = row.get("id", "unknown")

        default_commands_raw = row.get("default_commands", [])
        default_commands = [WorkflowStep(cmd) for cmd in default_commands_raw]

        sandbox_type_raw = row.get("default_sandbox_type", "git_worktree")
        sandbox_type = SandboxType(sandbox_type_raw)

        return ConfiguredRepository(
            id=row["id"],
            repository_url=row["repository_url"],
            display_name=row.get("display_name"),
            owner=row.get("owner"),
            default_branch=row.get("default_branch"),
            is_verified=row.get("is_verified", False),
            last_verified_at=row.get("last_verified_at"),
            default_sandbox_type=sandbox_type,
            default_commands=default_commands,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    async def list_repositories(self) -> list[ConfiguredRepository]:
        if self.file_mode:
            return [self._file_row_to_model(row) for row in self._load_file_repos()]

        response = self.client.table(self.table_name).select("*").order("created_at", desc=True).execute()
        repositories = [self._row_to_model(row) for row in response.data]
        self._logger.info("repositories_listed", count=len(repositories))
        return repositories

    async def get_repository(self, repository_id: str) -> ConfiguredRepository | None:
        if self.file_mode:
            for repo in self._load_file_repos():
                if repo.get("id") == repository_id:
                    return self._file_row_to_model(repo)
            self._logger.info("repository_not_found", repository_id=repository_id)
            return None

        response = self.client.table(self.table_name).select("*").eq("id", repository_id).execute()
        if not response.data:
            self._logger.info("repository_not_found", repository_id=repository_id)
            return None
        repository = self._row_to_model(response.data[0])
        self._logger.info("repository_retrieved", repository_id=repository_id, repository_url=repository.repository_url)
        return repository

    async def create_repository(
        self,
        repository_url: str,
        display_name: str | None = None,
        owner: str | None = None,
        default_branch: str | None = None,
        is_verified: bool = False,
    ) -> ConfiguredRepository:
        if self.file_mode:
            repos = self._load_file_repos()
            repo_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            new_repo = {
                "id": repo_id,
                "repository_url": repository_url,
                "display_name": display_name,
                "owner": owner,
                "default_branch": default_branch,
                "is_verified": is_verified,
                "last_verified_at": now if is_verified else None,
                "default_sandbox_type": "git_worktree",
                "default_commands": [cmd.value for cmd in WorkflowStep],
                "created_at": now,
                "updated_at": now,
            }
            repos.insert(0, new_repo)
            self._save_file_repos(repos)
            self._logger.info(
                "repository_created_file",
                repository_id=repo_id,
                repository_url=repository_url,
                is_verified=is_verified,
            )
            return self._file_row_to_model(new_repo)

        data: dict[str, Any] = {
            "repository_url": repository_url,
            "display_name": display_name,
            "owner": owner,
            "default_branch": default_branch,
            "is_verified": is_verified,
        }
        if is_verified:
            data["last_verified_at"] = datetime.now(timezone.utc).isoformat()

        response = self.client.table(self.table_name).insert(data).execute()
        repository = self._row_to_model(response.data[0])
        self._logger.info(
            "repository_created",
            repository_id=repository.id,
            repository_url=repository_url,
            is_verified=is_verified,
        )
        return repository

    async def update_repository(
        self,
        repository_id: str,
        **updates: Any
    ) -> ConfiguredRepository | None:
        if self.file_mode:
            repos = self._load_file_repos()
            updated_repo = None
            for idx, repo in enumerate(repos):
                if repo.get("id") == repository_id:
                    repo.update(updates)
                    repo["updated_at"] = datetime.now(timezone.utc).isoformat()
                    repos[idx] = repo
                    updated_repo = repo
                    break
            if updated_repo:
                self._save_file_repos(repos)
                return self._file_row_to_model(updated_repo)
            self._logger.info("repository_not_found_for_update", repository_id=repository_id)
            return None

        prepared_updates: dict[str, Any] = {}
        for key, value in updates.items():
            if isinstance(value, SandboxType):
                prepared_updates[key] = value.value
            elif isinstance(value, list) and value and all(isinstance(item, WorkflowStep) for item in value):
                prepared_updates[key] = [step.value for step in value]
            else:
                prepared_updates[key] = value
        prepared_updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        response = (
            self.client.table(self.table_name)
            .update(prepared_updates)
            .eq("id", repository_id)
            .execute()
        )
        if not response.data:
            self._logger.info("repository_not_found_for_update", repository_id=repository_id)
            return None

        repository = self._row_to_model(response.data[0])
        self._logger.info("repository_updated", repository_id=repository_id, updated_fields=list(updates.keys()))
        return repository

    async def delete_repository(self, repository_id: str) -> bool:
        if self.file_mode:
            repos = self._load_file_repos()
            new_repos = [r for r in repos if r.get("id") != repository_id]
            if len(new_repos) != len(repos):
                self._save_file_repos(new_repos)
                self._logger.info("repository_deleted_file", repository_id=repository_id)
                return True
            self._logger.info("repository_not_found_for_delete", repository_id=repository_id)
            return False

        response = self.client.table(self.table_name).delete().eq("id", repository_id).execute()
        deleted = len(response.data) > 0
        if deleted:
            self._logger.info("repository_deleted", repository_id=repository_id)
        else:
            self._logger.info("repository_not_found_for_delete", repository_id=repository_id)
        return deleted
