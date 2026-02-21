from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from tasks.handlers.base import TaskHandler


class TaskConstraint(BaseModel):
    max_attempts: int = Field(default=1, ge=1)


class TaskOutput(BaseModel):
    type: str
    properties: dict[str, dict[str, str]]
    required: list[str]


class TaskInput(BaseModel):
    type: str
    properties: dict[str, dict[str, str]]
    required: list[str]


class TaskSpec(BaseModel):
    id: str
    handler: str
    goal: str
    inputs: TaskInput
    tools_allowed: list[str]
    constraints: TaskConstraint
    outputs: TaskOutput


class TaskRegistry:
    def __init__(self, task_dir: Path):
        self._task_dir = task_dir
        self._tasks = self._load(task_dir)
        self._handlers = self._load_handlers(self._tasks)

    def get(self, task_id: str) -> TaskSpec:
        if task_id not in self._tasks:
            known = ", ".join(sorted(self._tasks))
            raise KeyError(f"Unknown task_id '{task_id}'. Known tasks: {known}")
        return self._tasks[task_id]

    def list_ids(self) -> list[str]:
        return sorted(self._tasks.keys())

    def get_handler(self, task_id: str) -> TaskHandler:
        if task_id not in self._handlers:
            known = ", ".join(sorted(self._handlers))
            raise KeyError(f"Unknown task_id '{task_id}'. Known handlers: {known}")
        return self._handlers[task_id]

    def get_handler_map(self) -> dict[str, TaskHandler]:
        return dict(self._handlers)

    @staticmethod
    def _load(task_dir: Path) -> dict[str, TaskSpec]:
        tasks: dict[str, TaskSpec] = {}
        for path in sorted(task_dir.glob("*.yaml")):
            with path.open("r", encoding="utf-8") as file_obj:
                raw = yaml.safe_load(file_obj)
            spec = TaskSpec.model_validate(raw)
            tasks[spec.id] = spec
        return tasks

    @staticmethod
    def _load_handlers(tasks: dict[str, TaskSpec]) -> dict[str, TaskHandler]:
        handlers: dict[str, TaskHandler] = {}
        for task_id, spec in tasks.items():
            handlers[task_id] = _build_handler(spec)
        return handlers


def _build_handler(spec: TaskSpec) -> TaskHandler:
    module_name, _, class_name = spec.handler.rpartition(".")
    if not module_name or not class_name:
        raise ValueError(
            f"Invalid handler path '{spec.handler}' for task_id '{spec.id}'. "
            "Expected format '<module>.<ClassName>'."
        )

    module = import_module(module_name)
    handler_class = getattr(module, class_name, None)
    if handler_class is None:
        raise ValueError(f"Handler class '{class_name}' was not found in module '{module_name}'.")

    handler = handler_class()
    resolved_task_id = getattr(handler, "task_id", None)
    if resolved_task_id != spec.id:
        raise ValueError(
            f"Handler '{spec.handler}' has task_id '{resolved_task_id}', expected '{spec.id}'."
        )
    return handler
