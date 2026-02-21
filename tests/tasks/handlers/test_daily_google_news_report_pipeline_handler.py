from pathlib import Path
from typing import Any

from tasks.handlers.daily_google_news_report_pipeline import DailyGoogleNewsReportPipelineHandler
from tasks.registry import TaskRegistry, TaskSpec


class FakeHandler:
    def __init__(self, result: dict[str, Any]):
        self._result = result

    def validate_payload(self, payload: dict[str, Any], spec: TaskSpec) -> dict[str, Any]:
        del spec
        return payload

    def execute(self, payload: dict[str, Any], spec: TaskSpec) -> dict[str, Any]:
        del payload, spec
        return self._result


def test_pipeline_handler_runs_steps(tmp_path: Path) -> None:
    output_path = tmp_path / "daily.md"

    handler = DailyGoogleNewsReportPipelineHandler()
    handler._fetch_handler = FakeHandler(  # type: ignore[assignment]
        {
            "fetched_at": "2026-02-18T00:00:00+00:00",
            "source_url": "https://news.ycombinator.com/",
            "raw_cards": [{"title": "A", "url": "u", "snippet": "s", "source": "x"}],
            "raw_html_path": "artifacts/raw.html",
        }
    )
    handler._extract_handler = FakeHandler(  # type: ignore[assignment]
        {
            "items_en": [
                {
                    "rank": 1,
                    "title_en": "A",
                    "summary_en": "B",
                    "source": "x",
                    "url": "u",
                }
            ],
            "selection_notes": "ok",
        }
    )
    handler._translate_handler = FakeHandler(  # type: ignore[assignment]
        {
            "output_path": str(output_path),
            "item_count": 1,
            "markdown_preview": "# preview",
            "report_date": "2026-02-18",
        }
    )

    spec = TaskRegistry(Path("configs/tasks")).get("daily_google_news_report_pipeline")
    payload = handler.validate_payload({}, spec)
    result = handler.execute(payload, spec)

    assert result["item_count"] == 1
    assert result["report_markdown_path"] == str(output_path)
    assert len(result["steps"]) == 3
    assert result["steps"][0]["status"] == "ok"
