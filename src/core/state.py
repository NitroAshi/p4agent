from typing import Any, TypedDict


class AgentState(TypedDict):
    task_id: str
    input_payload: dict[str, Any]
    plan: str
    llm_error: str | None
    tool_result: dict[str, Any] | None
    response: dict[str, Any] | None
    error: str | None
