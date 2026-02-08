from pathlib import Path

from tasks.registry import TaskRegistry


def test_task_registry_loads_task() -> None:
    registry = TaskRegistry(Path("configs/tasks"))
    loaded = registry.get("append_hello_agent_comment")

    assert loaded.id == "append_hello_agent_comment"
    assert "target_file" in loaded.inputs.properties
