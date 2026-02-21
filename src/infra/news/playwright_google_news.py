from __future__ import annotations

from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

_DEFAULT_URL = "https://news.ycombinator.com/"


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._current_href: str | None = None
        self._buffer: list[str] = []
        self.items: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attr_map = {key: value for key, value in attrs}
        href = attr_map.get("href")
        if isinstance(href, str) and href.strip():
            self._current_href = href.strip()
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            stripped = data.strip()
            if stripped:
                self._buffer.append(stripped)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self._current_href is None:
            return

        text = " ".join(self._buffer).strip()
        if text:
            self.items.append(
                {
                    "title": text,
                    "url": self._current_href,
                    "snippet": "",
                    "source": "",
                }
            )
        self._current_href = None
        self._buffer = []


def fetch_google_news_homepage(
    *,
    url: str,
    max_items: int,
    timeout_ms: int,
    snapshot_dir: str,
) -> dict[str, Any]:
    """Fetch Hacker News cards using Playwright, with HTML fallback parsing."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - depends on local environment
        raise RuntimeError(
            "Playwright is required for fetch_google_news_homepage. "
            "Install playwright and browsers."
        ) from exc

    cards: list[dict[str, str]] = []
    html = ""
    source_url = url or _DEFAULT_URL

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(source_url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(500)

        cards = _extract_cards_from_page(page=page, source_url=source_url, max_items=max_items)
        html = page.content()
        browser.close()

    if not cards:
        cards = extract_cards_from_html(html=html, source_url=source_url, max_items=max_items)

    snapshot_path = _write_html_snapshot(snapshot_dir=snapshot_dir, html=html)
    return {
        "fetched_at": datetime.now(UTC).isoformat(),
        "source_url": source_url,
        "raw_cards": cards,
        "raw_html_path": snapshot_path,
    }


def _extract_cards_from_page(*, page: Any, source_url: str, max_items: int) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    row_locator = page.locator("tr.athing")
    row_count = min(row_locator.count(), max_items * 3)

    for index in range(row_count):
        row = row_locator.nth(index)
        title = _safe_text(row, "span.titleline > a")
        href = _safe_attr(row, "span.titleline > a", "href")
        subtext = row.locator("xpath=following-sibling::tr[1]").first
        snippet = _safe_text(subtext, ".score")
        if not snippet:
            comments = _safe_text(subtext, "a[href^='item?id=']")
            snippet = comments
        if not title or not href:
            continue

        cards.append(
            {
                "title": title,
                "url": urljoin(source_url, href),
                "snippet": snippet,
                "source": "Hacker News",
            }
        )
        if len(cards) >= max_items:
            break

    return cards


def _safe_text(node: Any, selector: str) -> str:
    try:
        found = node.locator(selector).first
        if found.count() == 0:
            return ""
        text = found.inner_text().strip()
        return " ".join(text.split())
    except Exception:
        return ""


def _safe_attr(node: Any, selector: str, attribute: str) -> str:
    try:
        found = node.locator(selector).first
        if found.count() == 0:
            return ""
        value = found.get_attribute(attribute)
        return value.strip() if isinstance(value, str) else ""
    except Exception:
        return ""


def extract_cards_from_html(*, html: str, source_url: str, max_items: int) -> list[dict[str, str]]:
    parser = _AnchorParser()
    parser.feed(html)

    cards: list[dict[str, str]] = []
    for item in parser.items:
        title = item["title"].strip()
        href = item["url"].strip()
        if not title or not href:
            continue

        cards.append(
            {
                "title": title,
                "url": urljoin(source_url, href),
                "snippet": item.get("snippet", ""),
                "source": item.get("source", "Hacker News") or "Hacker News",
            }
        )
        if len(cards) >= max_items:
            break

    return cards


def _write_html_snapshot(*, snapshot_dir: str, html: str) -> str:
    directory = Path(snapshot_dir)
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"hacker_news_home_{timestamp}.html"
    path.write_text(html, encoding="utf-8")
    return str(path)


__all__ = ["extract_cards_from_html", "fetch_google_news_homepage"]
