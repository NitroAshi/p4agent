from __future__ import annotations

from pathlib import Path
from typing import Any

from infra.fs import append_text
from infra.llm.chains import CommentNormChain
from tasks.handlers.base import TaskHandler
from tasks.registry import TaskSpec


class AppendHelloAgentCommentHandler(TaskHandler):
    task_id = "append_hello_agent_comment"
    requires_llm = True

    def preprocess_with_llm(
        self,
        *,
        payload: dict[str, Any],
        spec: TaskSpec,
        llm_enabled: bool,
        llm_fallback_to_rules: bool,
        comment_chain: CommentNormChain | None,
    ) -> tuple[dict[str, Any], str | None, str | None]:
        if not llm_enabled:
            return payload, None, None

        if comment_chain is None:
            error_message = "LLM chain was not initialized"
            fatal_error = error_message if not llm_fallback_to_rules else None
            return payload, error_message, fatal_error

        try:
            target_file = str(payload["target_file"])
            generated = comment_chain.run(task_goal=spec.goal, target_file=target_file)
            next_payload = {**payload, "comment_text": generated.comment_text}
            return next_payload, None, None
        except Exception as exc:
            error_message = f"LLM generation failed: {exc}"
            fatal_error = error_message if not llm_fallback_to_rules else None
            return payload, error_message, fatal_error

    def execute(self, payload: dict[str, Any], spec: TaskSpec) -> dict[str, Any]:
        target_file = str(payload["target_file"])
        comment_text = self._resolve_comment_text(
            payload=payload,
            task_goal=spec.goal,
            target_file=target_file,
        )
        return append_text(target_file=target_file, text=comment_text)

    def _resolve_comment_text(
        self,
        *,
        payload: dict[str, Any],
        task_goal: str,
        target_file: str,
    ) -> str:
        maybe_generated = payload.get("comment_text")
        if isinstance(maybe_generated, str) and maybe_generated.strip():
            return self._normalize_comment_line(maybe_generated)

        return self._build_default_comment(task_goal=task_goal, target_file=target_file)

    @staticmethod
    def _build_default_comment(*, task_goal: str, target_file: str) -> str:
        filename = Path(target_file).name
        goal_text = " ".join(task_goal.strip().split())
        fallback = f"# p4agent fallback: {goal_text} ({filename})"
        return AppendHelloAgentCommentHandler._normalize_comment_line(fallback)

    @staticmethod
    def _normalize_comment_line(raw_comment: str) -> str:
        normalized = " ".join(raw_comment.strip().split())
        if not normalized.startswith("#"):
            normalized = f"# {normalized}"
        elif not normalized.startswith("# "):
            normalized = f"# {normalized.lstrip('#').strip()}"
        return normalized
