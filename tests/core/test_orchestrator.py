from pathlib import Path

from core.orchestrator import AgentOrchestrator
from tasks.registry import TaskRegistry


def test_graph_appends_comment(tmp_path: Path) -> None:
    target = tmp_path / "demo.py"
    target.write_text("print('x')\n", encoding="utf-8")

    orchestrator = AgentOrchestrator(TaskRegistry(Path("configs/tasks")))
    end_state = orchestrator.invoke(
        task_id="append_hello_agnet_comment",
        payload={"target_file": str(target)},
    )

    content = target.read_text(encoding="utf-8")
    assert "# hello agnet" in content
    assert end_state["response"] is not None
    assert end_state["response"]["status"] == "ok"
