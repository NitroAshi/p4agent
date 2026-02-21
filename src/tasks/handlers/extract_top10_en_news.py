from __future__ import annotations

from typing import Any

from core.settings import settings
from infra.llm.factory import build_llm_adapter
from infra.llm.news_chains import NewsExtractChain
from tasks.handlers.base import TaskHandler
from tasks.registry import TaskSpec


class ExtractTop10EnNewsHandler(TaskHandler):
    task_id = "extract_top10_en_news"

    def execute(self, payload: dict[str, Any], spec: TaskSpec) -> dict[str, Any]:
        del spec
        raw_cards = payload.get("raw_cards")
        if not isinstance(raw_cards, list):
            raise ValueError("raw_cards must be an array")

        top_k = int(payload.get("top_k") or 10)
        if top_k <= 0:
            raise ValueError("top_k must be > 0")

        if not settings.llm_enabled:
            raise RuntimeError("LLM is required for extract_top10_en_news")

        adapter = build_llm_adapter(settings)
        chain = NewsExtractChain(adapter)
        output = chain.run(raw_cards=_coerce_raw_cards(raw_cards), top_k=top_k)

        normalized_items = _normalize_items(output.model_dump().get("items_en", []), top_k=top_k)
        return {
            "items_en": normalized_items,
            "selection_notes": output.selection_notes,
        }


def _coerce_raw_cards(raw_cards: list[Any]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in raw_cards:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "title": str(item.get("title") or ""),
                "url": str(item.get("url") or ""),
                "snippet": str(item.get("snippet") or ""),
                "source": str(item.get("source") or ""),
            }
        )
    return normalized


def _normalize_items(items: list[dict[str, Any]], *, top_k: int) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for item in items:
        url = str(item.get("url") or "").strip()
        title = str(item.get("title_en") or "").strip()
        if not url and not title:
            continue

        key = f"{url.lower()}::{title.lower()}"
        if key in seen_keys:
            continue
        seen_keys.add(key)

        deduped.append(
            {
                "rank": len(deduped) + 1,
                "title_en": title,
                "summary_en": str(item.get("summary_en") or "").strip(),
                "source": str(item.get("source") or "").strip(),
                "url": url,
            }
        )
        if len(deduped) >= top_k:
            break

    return deduped
