import argparse
import json
import sys

import pytest

from app import cli


def test_parse_args_with_target_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["p4agent-cli", "--task-id", "append_hello_agent_comment", "--target-file", "demo.py"],
    )

    args = cli.parse_args()

    assert args.task_id == "append_hello_agent_comment"
    assert args.target_file == "demo.py"


def test_build_payload_from_input_json() -> None:
    args = argparse.Namespace(input_json='{"target_file":"x.py"}', target_file=None)

    payload = cli.build_payload(args)

    assert payload == {"target_file": "x.py"}


def test_build_payload_rejects_non_object_json() -> None:
    args = argparse.Namespace(input_json="[1,2,3]", target_file=None)

    with pytest.raises(ValueError, match="must decode to a JSON object"):
        cli.build_payload(args)


def test_build_payload_from_target_file() -> None:
    args = argparse.Namespace(input_json=None, target_file="abc.py")

    payload = cli.build_payload(args)

    assert payload == {"target_file": "abc.py"}


def test_build_payload_requires_input() -> None:
    args = argparse.Namespace(input_json=None, target_file=None)

    with pytest.raises(ValueError, match="Provide either"):
        cli.build_payload(args)


def test_main_prints_result(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class FakeService:
        def run_task(self, task_id: str, payload: dict[str, object]) -> dict[str, object]:
            assert task_id == "append_hello_agent_comment"
            assert payload == {"target_file": "demo.py"}
            return {"status": "ok", "task_id": task_id}

    monkeypatch.setattr(
        cli,
        "parse_args",
        lambda: argparse.Namespace(
            task_id="append_hello_agent_comment",
            input_json=None,
            target_file="demo.py",
        ),
    )
    monkeypatch.setattr(cli, "AgentService", FakeService)

    cli.main()

    out = capsys.readouterr().out
    assert json.loads(out) == {"status": "ok", "task_id": "append_hello_agent_comment"}
