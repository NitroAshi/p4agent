from __future__ import annotations

from collections.abc import Mapping

from tasks.handlers.base import TaskHandler


class RouteNotFoundError(KeyError):
    pass


class TaskRouter:
    def __init__(self, handlers: Mapping[str, TaskHandler]):
        self._handlers = dict(handlers)

    def route(self, task_id: str) -> TaskHandler:
        handler = self._handlers.get(task_id)
        if handler is None:
            known = ", ".join(sorted(self._handlers))
            raise RouteNotFoundError(f"No handler for task_id '{task_id}'. Known handlers: {known}")
        return handler

    def list_ids(self) -> list[str]:
        return sorted(self._handlers)
