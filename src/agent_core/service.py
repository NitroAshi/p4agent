from typing import Any

from agent_core.config import settings
from agent_core.graph import AgentGraph
from agent_core.tasks import TaskRegistry


class AgentService:
    """Application-facing service wrapper around the agent graph."""

    def __init__(self) -> None:
        self._task_registry = TaskRegistry(settings.task_config_dir)
        self._graph = AgentGraph(task_registry=self._task_registry)

    def run_task(self, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        end_state = self._graph.invoke(task_id=task_id, payload=payload)
        response = end_state["response"]
        if response is None:
            return {"status": "failed", "error": "Agent did not produce a response"}
        return response

    def list_tasks(self) -> list[str]:
        return self._task_registry.list_ids()
