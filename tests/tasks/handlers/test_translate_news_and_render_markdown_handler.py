from pathlib import Path
from typing import Any

import pytest

import tasks.handlers.translate_news_and_render_markdown as handler_module
from core.settings import settings
from infra.llm.news_schema import NewsTranslateOutput, TranslatedNewsItem
from tasks.handlers.translate_news_and_render_markdown import TranslateNewsAndRenderMarkdownHandler
from tasks.registry import TaskRegistry


class FakeTranslateChain:
    def __init__(self, adapter: Any):
        del adapter

    def run(self, *, items_en: list[dict[str, str]], date: str) -> NewsTranslateOutput:
        del items_en, date
        return NewsTranslateOutput(
            items=[
                TranslatedNewsItem(
                    rank=1,
                    title_en="Title EN",
                    summary_en="Summary EN",
                    title_zh="Title ZH",
                    summary_zh="Summary ZH",
                    title_ja="Title JA",
                    summary_ja="Summary JA",
                    source="Source",
                    url="https://example.com/1",
                )
            ]
        )


class RetryOnceTranslateChain:
    def __init__(self, adapter: Any):
        del adapter
        self.calls = 0

    def run(self, *, items_en: list[dict[str, str]], date: str) -> NewsTranslateOutput:
        del items_en, date
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("Request timed out.")
        return NewsTranslateOutput(
            items=[
                TranslatedNewsItem(
                    rank=1,
                    title_en="Title EN",
                    summary_en="Summary EN",
                    title_zh="Title ZH",
                    summary_zh="Summary ZH",
                    title_ja="Title JA",
                    summary_ja="Summary JA",
                    source="Source",
                    url="https://example.com/1",
                )
            ]
        )


def test_translate_handler_renders_markdown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "llm_enabled", True)
    monkeypatch.setattr(handler_module, "build_llm_adapter", lambda _: object())
    monkeypatch.setattr(handler_module, "NewsTranslateChain", FakeTranslateChain)

    handler = TranslateNewsAndRenderMarkdownHandler()
    spec = TaskRegistry(Path("configs/tasks")).get("translate_news_and_render_markdown")
    output_path = tmp_path / "news.md"
    payload = handler.validate_payload(
        {
            "items_en": [
                {
                    "rank": 1,
                    "title_en": "Title EN",
                    "summary_en": "Summary EN",
                    "source": "Source",
                    "url": "https://example.com/1",
                }
            ],
            "date": "2026-02-18",
            "output_path": str(output_path),
        },
        spec,
    )

    result = handler.execute(payload, spec)

    text = output_path.read_text(encoding="utf-8")
    assert result["item_count"] == 1
    assert "Daily Hacker News Digest" in text
    assert "English" in text


def test_translate_handler_retries_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "llm_enabled", True)
    monkeypatch.setattr(handler_module, "build_llm_adapter", lambda _: object())
    monkeypatch.setattr(handler_module, "NewsTranslateChain", RetryOnceTranslateChain)
    monkeypatch.setattr(handler_module, "sleep", lambda _: None)

    handler = TranslateNewsAndRenderMarkdownHandler()
    spec = TaskRegistry(Path("configs/tasks")).get("translate_news_and_render_markdown")
    output_path = tmp_path / "retry_news.md"
    payload = handler.validate_payload(
        {
            "items_en": [
                {
                    "rank": 1,
                    "title_en": "Title EN",
                    "summary_en": "Summary EN",
                    "source": "Source",
                    "url": "https://example.com/1",
                }
            ],
            "date": "2026-02-19",
            "output_path": str(output_path),
            "translate_max_retries": 2,
            "translate_retry_seconds": 1,
        },
        spec,
    )

    result = handler.execute(payload, spec)

    assert result["item_count"] == 1
    assert output_path.exists()


def test_translate_handler_requires_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_enabled", False)

    handler = TranslateNewsAndRenderMarkdownHandler()
    spec = TaskRegistry(Path("configs/tasks")).get("translate_news_and_render_markdown")
    payload = handler.validate_payload(
        {
            "items_en": [
                {
                    "rank": 1,
                    "title_en": "Title EN",
                    "summary_en": "Summary EN",
                    "source": "Source",
                    "url": "https://example.com/1",
                }
            ]
        },
        spec,
    )

    with pytest.raises(RuntimeError, match="LLM is required"):
        handler.execute(payload, spec)
