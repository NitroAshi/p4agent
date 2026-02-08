from pathlib import Path

from core.service import AgentService


def test_service_run_task(tmp_path: Path) -> None:
    target = tmp_path / "integration_demo.py"
    target.write_text("value = 1\n", encoding="utf-8")

    service = AgentService()
    result = service.run_task(
        task_id="append_hello_agnet_comment",
        payload={"target_file": str(target)},
    )

    assert result["status"] == "ok"
    assert result["task_id"] == "append_hello_agnet_comment"
