from __future__ import annotations

from time import perf_counter
from typing import Any, Protocol

from core.settings import settings
from tasks.handlers.base import TaskHandler
from tasks.handlers.extract_top10_en_news import ExtractTop10EnNewsHandler
from tasks.handlers.fetch_google_news_homepage import FetchGoogleNewsHomepageHandler
from tasks.handlers.translate_news_and_render_markdown import (
    TranslateNewsAndRenderMarkdownHandler,
)
from tasks.registry import TaskRegistry, TaskSpec


class DailyGoogleNewsReportPipelineHandler(TaskHandler):
    task_id = "daily_google_news_report_pipeline"

    def __init__(self) -> None:
        self._fetch_handler = FetchGoogleNewsHomepageHandler()
        self._extract_handler = ExtractTop10EnNewsHandler()
        self._translate_handler = TranslateNewsAndRenderMarkdownHandler()

    def execute(self, payload: dict[str, Any], spec: TaskSpec) -> dict[str, Any]:
        del spec
        registry = TaskRegistry(settings.task_config_dir)
        fetch_spec = registry.get("fetch_google_news_homepage")
        extract_spec = registry.get("extract_top10_en_news")
        translate_spec = registry.get("translate_news_and_render_markdown")

        steps: list[dict[str, Any]] = []

        fetch_payload = {
            "url": payload.get("url"),
            "max_items": payload.get("max_items"),
            "timeout_ms": payload.get("timeout_ms"),
            "snapshot_dir": payload.get("snapshot_dir"),
        }
        fetch_result = self._run_step(
            name="fetch_google_news_homepage",
            steps=steps,
            fn=lambda: self._fetch_handler.execute(
                self._fetch_handler.validate_payload(_strip_none(fetch_payload), fetch_spec),
                fetch_spec,
            ),
        )

        extract_payload = {
            "raw_cards": fetch_result["raw_cards"],
            "top_k": payload.get("max_items") or 10,
        }
        extract_result = self._run_step(
            name="extract_top10_en_news",
            steps=steps,
            fn=lambda: self._extract_handler.execute(
                self._extract_handler.validate_payload(_strip_none(extract_payload), extract_spec),
                extract_spec,
            ),
        )

        translate_payload = {
            "items_en": extract_result["items_en"],
            "date": payload.get("date"),
            "timezone": payload.get("timezone"),
            "output_path": payload.get("output_path"),
            "translate_batch_size": payload.get("translate_batch_size"),
            "translate_max_retries": payload.get("translate_max_retries"),
            "translate_retry_seconds": payload.get("translate_retry_seconds"),
        }
        translate_result = self._run_step(
            name="translate_news_and_render_markdown",
            steps=steps,
            fn=lambda: self._translate_handler.execute(
                self._translate_handler.validate_payload(
                    _strip_none(translate_payload),
                    translate_spec,
                ),
                translate_spec,
            ),
        )

        return {
            "report_markdown_path": translate_result["output_path"],
            "report_date": translate_result["report_date"],
            "item_count": translate_result["item_count"],
            "steps": steps,
            "source_url": fetch_result["source_url"],
            "selection_notes": extract_result.get("selection_notes"),
            "markdown_preview": translate_result["markdown_preview"],
        }

    def _run_step(
        self,
        *,
        name: str,
        steps: list[dict[str, Any]],
        fn: CallableNoArg,
    ) -> dict[str, Any]:
        started = perf_counter()
        try:
            result = fn()
        except Exception as exc:
            elapsed_ms = int((perf_counter() - started) * 1000)
            steps.append(
                {
                    "name": name,
                    "status": "failed",
                    "duration_ms": elapsed_ms,
                    "error": str(exc),
                }
            )
            raise RuntimeError(f"Step '{name}' failed: {exc}") from exc

        elapsed_ms = int((perf_counter() - started) * 1000)
        steps.append(
            {
                "name": name,
                "status": "ok",
                "duration_ms": elapsed_ms,
            }
        )
        return result


class CallableNoArg(Protocol):
    def __call__(self) -> dict[str, Any]: ...


def _strip_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}
