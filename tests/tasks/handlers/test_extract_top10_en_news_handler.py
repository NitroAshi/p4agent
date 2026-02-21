from pathlib import Path
from typing import Any, cast

import pytest

import tasks.handlers.extract_top10_en_news as handler_module
from core.settings import settings
from infra.llm.news_schema import ExtractedNewsItem, NewsExtractOutput
from tasks.handlers.extract_top10_en_news import ExtractTop10EnNewsHandler
from tasks.registry import TaskRegistry


class FakeExtractChain:
    def __init__(self, adapter: Any):
        del adapter

    def run(self, *, raw_cards: list[dict[str, str]], top_k: int) -> NewsExtractOutput:
        del raw_cards, top_k
        return NewsExtractOutput(
            items_en=[
                ExtractedNewsItem(
                    rank=1,
                    title_en="A",
                    summary_en="S1",
                    source="SRC",
                    url="https://example.com/1",
                ),
                ExtractedNewsItem(
                    rank=2,
                    title_en="A",
                    summary_en="S1 dup",
                    source="SRC",
                    url="https://example.com/1",
                ),
            ],
            selection_notes="deduped",
        )


def test_extract_handler_runs_chain_and_dedupes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_enabled", True)
    monkeypatch.setattr(handler_module, "build_llm_adapter", lambda _: object())
    monkeypatch.setattr(handler_module, "NewsExtractChain", FakeExtractChain)

    handler = ExtractTop10EnNewsHandler()
    spec = TaskRegistry(Path("configs/tasks")).get("extract_top10_en_news")
    payload = handler.validate_payload(
        {"raw_cards": [{"title": "x", "url": "u", "snippet": "s", "source": "src"}]},
        spec,
    )

    result = handler.execute(payload, spec)

    assert len(cast(list[dict[str, Any]], result["items_en"])) == 1
    assert result["selection_notes"] == "deduped"


def test_extract_handler_requires_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_enabled", False)

    handler = ExtractTop10EnNewsHandler()
    spec = TaskRegistry(Path("configs/tasks")).get("extract_top10_en_news")
    payload = handler.validate_payload({"raw_cards": []}, spec)

    with pytest.raises(RuntimeError, match="LLM is required"):
        handler.execute(payload, spec)
