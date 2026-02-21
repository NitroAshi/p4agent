from typing import Any

from core.orchestrator import AgentOrchestrator
from core.routing import TaskRouter
from core.settings import settings
from tasks.registry import TaskRegistry


class AgentService:
    """Application-facing service wrapper around the agent graph."""

    def __init__(self) -> None:
        self._task_registry = TaskRegistry(settings.task_config_dir)
        self._task_router = TaskRouter(self._task_registry.get_handler_map())
        self._ensure_routes_cover_registry()
        self._orchestrator = AgentOrchestrator(
            task_registry=self._task_registry,
            task_router=self._task_router,
        )

    def run_task(self, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        end_state = self._orchestrator.invoke(task_id=task_id, payload=payload)
        response = end_state["response"]
        if response is None:
            return {
                "status": "failed",
                "task_id": task_id,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Agent did not produce a response",
                },
            }
        return response

    def list_tasks(self) -> list[str]:
        registry_ids = set(self._task_registry.list_ids())
        routed_ids = set(self._task_router.list_ids())
        return sorted(registry_ids & routed_ids)

    def _ensure_routes_cover_registry(self) -> None:
        registry_ids = set(self._task_registry.list_ids())
        routed_ids = set(self._task_router.list_ids())
        missing_routes = sorted(registry_ids - routed_ids)
        missing_specs = sorted(routed_ids - registry_ids)
        if missing_routes or missing_specs:
            raise ValueError(
                f"Router and registry mismatch. missing_routes={missing_routes}, "
                f"missing_specs={missing_specs}"
            )
