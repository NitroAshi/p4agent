from __future__ import annotations

from typing import Any

from infra.news.playwright_google_news import fetch_google_news_homepage
from tasks.handlers.base import TaskHandler
from tasks.registry import TaskSpec

_DEFAULT_URL = "https://news.ycombinator.com/"


class FetchGoogleNewsHomepageHandler(TaskHandler):
    task_id = "fetch_google_news_homepage"

    def execute(self, payload: dict[str, Any], spec: TaskSpec) -> dict[str, Any]:
        del spec
        url = str(payload.get("url") or _DEFAULT_URL)
        max_items = int(payload.get("max_items") or 10)
        timeout_ms = int(payload.get("timeout_ms") or 30000)
        snapshot_dir = str(payload.get("snapshot_dir") or "artifacts/news_raw")

        if max_items <= 0:
            raise ValueError("max_items must be > 0")

        return fetch_google_news_homepage(
            url=url,
            max_items=max_items,
            timeout_ms=timeout_ms,
            snapshot_dir=snapshot_dir,
        )
