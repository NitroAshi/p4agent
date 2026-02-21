from typing import Any, TypedDict

from tasks.handlers.base import TaskHandler
from tasks.registry import TaskSpec


class AgentState(TypedDict):
    task_id: str
    input_payload: dict[str, Any]
    task_spec: TaskSpec | None
    handler: TaskHandler | None
    validated_payload: dict[str, Any] | None
    plan: str
    llm_error: str | None
    execution_result: dict[str, Any] | None
    response: dict[str, Any] | None
    error_code: str | None
    error_message: str | None
