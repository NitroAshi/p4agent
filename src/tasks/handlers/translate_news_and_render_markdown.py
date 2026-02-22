from __future__ import annotations

from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Any
from zoneinfo import ZoneInfo

from core.settings import settings
from infra.llm.factory import build_llm_adapter
from infra.llm.news_chains import NewsTranslateChain
from tasks.handlers.base import TaskHandler
from tasks.registry import TaskSpec

_DEFAULT_TIMEZONE = "Asia/Shanghai"
_DEFAULT_BATCH_SIZE = 3
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_RETRY_SECONDS = 2


class TranslateNewsAndRenderMarkdownHandler(TaskHandler):
    task_id = "translate_news_and_render_markdown"

    def execute(self, payload: dict[str, Any], spec: TaskSpec) -> dict[str, Any]:
        del spec
        items_en_raw = payload.get("items_en")
        if not isinstance(items_en_raw, list):
            raise ValueError("items_en must be an array")

        items_en = _coerce_items_en(items_en_raw)
        if not items_en:
            raise ValueError("items_en cannot be empty")

        timezone_name = str(payload.get("timezone") or _DEFAULT_TIMEZONE)
        report_date = str(payload.get("date") or _today_in_timezone(timezone_name))
        output_path = str(payload.get("output_path") or f"artifacts/news_{report_date}.md")
        batch_size = int(payload.get("translate_batch_size") or _DEFAULT_BATCH_SIZE)
        max_retries = int(payload.get("translate_max_retries") or _DEFAULT_MAX_RETRIES)
        retry_seconds = int(payload.get("translate_retry_seconds") or _DEFAULT_RETRY_SECONDS)

        if not settings.llm_enabled:
            raise RuntimeError("LLM is required for translate_news_and_render_markdown")
        if batch_size <= 0:
            raise ValueError("translate_batch_size must be > 0")
        if max_retries <= 0:
            raise ValueError("translate_max_retries must be > 0")
        if retry_seconds <= 0:
            raise ValueError("translate_retry_seconds must be > 0")

        adapter = build_llm_adapter(settings)
        chain = NewsTranslateChain(adapter)
        translated_items = _run_translate_in_batches(
            chain=chain,
            items_en=items_en,
            report_date=report_date,
            batch_size=batch_size,
            max_retries=max_retries,
            retry_seconds=retry_seconds,
        )

        markdown = _render_markdown(
            report_date=report_date,
            timezone_name=timezone_name,
            items=translated_items,
        )

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")

        preview = "\n".join(markdown.splitlines()[:12])
        return {
            "output_path": str(output_file),
            "item_count": len(translated_items),
            "markdown_preview": preview,
            "report_date": report_date,
        }


def _today_in_timezone(timezone_name: str) -> str:
    try:
        zone = ZoneInfo(timezone_name)
    except Exception:
        zone = ZoneInfo("UTC")
    return datetime.now(zone).strftime("%Y-%m-%d")


def _coerce_items_en(items_en_raw: list[Any]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for index, item in enumerate(items_en_raw, start=1):
        if not isinstance(item, dict):
            continue
        items.append(
            {
                "rank": str(item.get("rank") or index),
                "title_en": str(item.get("title_en") or ""),
                "summary_en": str(item.get("summary_en") or ""),
                "source": str(item.get("source") or ""),
                "url": str(item.get("url") or ""),
            }
        )
    return items


def _run_translate_in_batches(
    *,
    chain: NewsTranslateChain,
    items_en: list[dict[str, str]],
    report_date: str,
    batch_size: int,
    max_retries: int,
    retry_seconds: int,
) -> list[dict[str, Any]]:
    translated_items: list[dict[str, Any]] = []
    for start in range(0, len(items_en), batch_size):
        batch = items_en[start : start + batch_size]
        translated_items.extend(
            _translate_one_batch(
                chain=chain,
                batch=batch,
                report_date=report_date,
                max_retries=max_retries,
                retry_seconds=retry_seconds,
            )
        )

    translated_items.sort(key=lambda item: int(item.get("rank", 0)))
    return translated_items


def _translate_one_batch(
    *,
    chain: NewsTranslateChain,
    batch: list[dict[str, str]],
    report_date: str,
    max_retries: int,
    retry_seconds: int,
) -> list[dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            translated = chain.run(items_en=batch, date=report_date)
            raw_items = translated.model_dump().get("items", [])
            if not isinstance(raw_items, list):
                raise RuntimeError("Translated response must contain list items")
            return [item for item in raw_items if isinstance(item, dict)]
        except Exception as exc:
            last_error = exc
            if attempt >= max_retries or not _is_retryable_error(exc):
                break
            sleep(retry_seconds * attempt)

    if last_error is None:
        raise RuntimeError("Translation failed with unknown error")
    raise last_error


def _is_retryable_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "429" in text or "rate limit" in text or "timed out" in text or "timeout" in text


def _render_markdown(*, report_date: str, timezone_name: str, items: list[dict[str, Any]]) -> str:
    lines: list[str] = [
        f"# Daily Hacker News Digest ({report_date})",
        "",
        f"- Timezone: `{timezone_name}`",
        f"- Total items: `{len(items)}`",
        "",
    ]

    if len(items) < 10:
        lines.extend(
            [
                f"> Note: only `{len(items)}` items were available (< 10).",
                "",
            ]
        )

    for item in items:
        rank = item.get("rank", "")
        lines.extend(
            [
                f"## {rank}. {item.get('title_en', '')}",
                "",
                "**English**",
                f"- Title: {item.get('title_en', '')}",
                f"- Summary: {item.get('summary_en', '')}",
                "",
                "**Chinese (zh-CN)**",
                f"- Title: {item.get('title_zh', '')}",
                f"- Summary: {item.get('summary_zh', '')}",
                "",
                "**Japanese (ja-JP)**",
                f"- Title: {item.get('title_ja', '')}",
                f"- Summary: {item.get('summary_ja', '')}",
                "",
                f"- Source: {item.get('source', '')}",
                f"- URL: {item.get('url', '')}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"
