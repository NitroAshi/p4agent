from pathlib import Path

import pytest

import core.orchestrator as orchestrator_module
from core.orchestrator import AgentOrchestrator
from core.routing import TaskRouter
from core.settings import settings
from tasks.registry import TaskRegistry


def _build_orchestrator() -> AgentOrchestrator:
    registry = TaskRegistry(Path("configs/tasks"))
    router = TaskRouter(registry.get_handler_map())
    return AgentOrchestrator(registry, router)


def test_graph_appends_comment(tmp_path: Path) -> None:
    target = tmp_path / "demo.py"
    target.write_text("print('x')\n", encoding="utf-8")

    orchestrator = _build_orchestrator()
    end_state = orchestrator.invoke(
        task_id="append_hello_agent_comment",
        payload={"target_file": str(target)},
    )

    content = target.read_text(encoding="utf-8")
    assert "# hello from p4agent" in content
    assert end_state["response"] is not None
    assert end_state["response"]["status"] == "ok"


def test_llm_bootstrap_failure_falls_back_to_rules(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_missing_key(_: object) -> object:
        raise ValueError("missing llm key")

    target = tmp_path / "demo_fallback.py"
    target.write_text("print('x')\n", encoding="utf-8")

    monkeypatch.setattr(settings, "llm_enabled", True)
    monkeypatch.setattr(settings, "llm_fallback_to_rules", True)
    monkeypatch.setattr(orchestrator_module, "build_llm_adapter", _raise_missing_key)

    orchestrator = _build_orchestrator()
    end_state = orchestrator.invoke(
        task_id="append_hello_agent_comment",
        payload={"target_file": str(target)},
    )

    content = target.read_text(encoding="utf-8")
    assert "# hello from p4agent" in content
    assert end_state["response"] is not None
    assert end_state["response"]["status"] == "ok"
    assert "llm_error" in end_state["response"]


def test_llm_bootstrap_failure_can_block_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_missing_key(_: object) -> object:
        raise ValueError("missing llm key")

    target = tmp_path / "demo_block.py"
    target.write_text("print('x')\n", encoding="utf-8")

    monkeypatch.setattr(settings, "llm_enabled", True)
    monkeypatch.setattr(settings, "llm_fallback_to_rules", False)
    monkeypatch.setattr(orchestrator_module, "build_llm_adapter", _raise_missing_key)

    orchestrator = _build_orchestrator()
    end_state = orchestrator.invoke(
        task_id="append_hello_agent_comment",
        payload={"target_file": str(target)},
    )

    content = target.read_text(encoding="utf-8")
    assert "# hello from p4agent" not in content
    assert end_state["response"] is not None
    assert end_state["response"]["status"] == "failed"
    assert end_state["response"]["error"]["code"] == "LLM_PREPROCESS_FAILED"


def test_invalid_payload_returns_structured_error() -> None:
    orchestrator = _build_orchestrator()
    end_state = orchestrator.invoke(task_id="append_hello_agent_comment", payload={})

    assert end_state["response"] is not None
    assert end_state["response"]["status"] == "failed"
    assert end_state["response"]["error"]["code"] == "INVALID_PAYLOAD"
