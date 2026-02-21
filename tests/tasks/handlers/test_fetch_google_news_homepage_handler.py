from pathlib import Path
from typing import Any

import pytest

import tasks.handlers.fetch_google_news_homepage as handler_module
from tasks.handlers.fetch_google_news_homepage import FetchGoogleNewsHomepageHandler
from tasks.registry import TaskRegistry


def test_fetch_handler_calls_scraper_with_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, Any] = {}

    def _fake_fetch(
        *,
        url: str,
        max_items: int,
        timeout_ms: int,
        snapshot_dir: str,
    ) -> dict[str, Any]:
        called.update(
            {
                "url": url,
                "max_items": max_items,
                "timeout_ms": timeout_ms,
                "snapshot_dir": snapshot_dir,
            }
        )
        return {
            "fetched_at": "2026-02-18T00:00:00+00:00",
            "source_url": url,
            "raw_cards": [],
            "raw_html_path": "artifacts/x.html",
        }

    monkeypatch.setattr(handler_module, "fetch_google_news_homepage", _fake_fetch)

    handler = FetchGoogleNewsHomepageHandler()
    spec = TaskRegistry(Path("configs/tasks")).get("fetch_google_news_homepage")
    payload = handler.validate_payload({}, spec)
    result = handler.execute(payload, spec)

    assert called["max_items"] == 10
    assert called["timeout_ms"] == 30000
    assert result["raw_html_path"].endswith(".html")
