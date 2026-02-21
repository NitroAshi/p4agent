from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from infra.llm.chains import CommentNormChain
from tasks.registry import TaskSpec
from tasks.validation import validate_task_payload


class TaskHandler(ABC):
    task_id: str
    requires_llm: bool = False

    def validate_payload(self, payload: dict[str, Any], spec: TaskSpec) -> dict[str, Any]:
        return validate_task_payload(spec, payload)

    def plan(self, payload: dict[str, Any], spec: TaskSpec) -> str:
        del payload
        return spec.goal

    def preprocess_with_llm(
        self,
        *,
        payload: dict[str, Any],
        spec: TaskSpec,
        llm_enabled: bool,
        llm_fallback_to_rules: bool,
        comment_chain: CommentNormChain | None,
    ) -> tuple[dict[str, Any], str | None, str | None]:
        del spec, llm_enabled, llm_fallback_to_rules, comment_chain
        return payload, None, None

    @abstractmethod
    def execute(self, payload: dict[str, Any], spec: TaskSpec) -> dict[str, Any]:
        raise NotImplementedError

    def format_response(
        self,
        *,
        spec: TaskSpec,
        result: dict[str, Any],
        llm_error: str | None,
    ) -> dict[str, Any]:
        response: dict[str, Any] = {
            "status": "ok",
            "task_id": spec.id,
            **result,
        }
        if llm_error is not None:
            response["llm_error"] = llm_error
        return response
