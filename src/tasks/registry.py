from pathlib import Path

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field


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
    goal: str
    inputs: TaskInput
    tools_allowed: list[str]
    constraints: TaskConstraint
    outputs: TaskOutput


class TaskRegistry:
    def __init__(self, task_dir: Path):
        self._task_dir = task_dir
        self._tasks = self._load(task_dir)

    def get(self, task_id: str) -> TaskSpec:
        if task_id not in self._tasks:
            known = ", ".join(sorted(self._tasks))
            raise KeyError(f"Unknown task_id '{task_id}'. Known tasks: {known}")
        return self._tasks[task_id]

    def list_ids(self) -> list[str]:
        return sorted(self._tasks.keys())

    @staticmethod
    def _load(task_dir: Path) -> dict[str, TaskSpec]:
        tasks: dict[str, TaskSpec] = {}
        for path in sorted(task_dir.glob("*.yaml")):
            with path.open("r", encoding="utf-8") as file_obj:
                raw = yaml.safe_load(file_obj)
            spec = TaskSpec.model_validate(raw)
            tasks[spec.id] = spec
        return tasks
