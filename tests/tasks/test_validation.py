from pathlib import Path

import pytest
from pydantic import ValidationError

from tasks.registry import TaskRegistry
from tasks.validation import validate_task_payload


def test_validation_accepts_valid_payload() -> None:
    spec = TaskRegistry(Path("configs/tasks")).get("append_hello_agent_comment")

    payload = validate_task_payload(spec, {"target_file": "demo.py"})

    assert payload["target_file"] == "demo.py"


def test_validation_rejects_missing_required() -> None:
    spec = TaskRegistry(Path("configs/tasks")).get("append_hello_agent_comment")

    with pytest.raises(ValidationError):
        validate_task_payload(spec, {})


def test_validation_rejects_extra_fields() -> None:
    spec = TaskRegistry(Path("configs/tasks")).get("append_hello_agent_comment")

    with pytest.raises(ValidationError):
        validate_task_payload(spec, {"target_file": "demo.py", "unexpected": True})
