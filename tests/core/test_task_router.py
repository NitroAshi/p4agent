from pathlib import Path

import pytest

from core.routing import RouteNotFoundError, TaskRouter
from tasks.handlers.append_hello_agent_comment import AppendHelloAgentCommentHandler
from tasks.registry import TaskRegistry


def _build_router() -> TaskRouter:
    registry = TaskRegistry(Path("configs/tasks"))
    return TaskRouter(registry.get_handler_map())


def test_route_known_task() -> None:
    router = _build_router()

    handler = router.route("append_hello_agent_comment")

    assert isinstance(handler, AppendHelloAgentCommentHandler)


def test_route_unknown_task_raises() -> None:
    router = _build_router()

    with pytest.raises(RouteNotFoundError, match="No handler for task_id"):
        router.route("missing_task")


def test_registry_tasks_have_route() -> None:
    registry = TaskRegistry(Path("configs/tasks"))
    router = TaskRouter(registry.get_handler_map())

    missing = set(registry.list_ids()) - set(router.list_ids())

    assert missing == set()


def test_router_lists_google_news_tasks() -> None:
    router = _build_router()

    assert "fetch_google_news_homepage" in router.list_ids()
    assert "extract_top10_en_news" in router.list_ids()
    assert "translate_news_and_render_markdown" in router.list_ids()
    assert "daily_google_news_report_pipeline" in router.list_ids()
