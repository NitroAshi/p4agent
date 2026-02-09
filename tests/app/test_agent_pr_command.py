from pathlib import Path

from app.agent_pr_command import OutputFormat, _write_output, parse_agent_pr_comment


def test_parse_valid_command() -> None:
    result = parse_agent_pr_comment("/agent-pr append_hello_agent_comment ./aaa.txt")

    assert result.valid is True
    assert result.command is not None
    assert result.command.task_id == "append_hello_agent_comment"
    assert result.command.target_file == "aaa.txt"


def test_parse_rejects_missing_prefix() -> None:
    result = parse_agent_pr_comment("append_hello_agent_comment ./aaa.txt")

    assert result.valid is False
    assert "must start" in (result.error_message or "")


def test_parse_rejects_unsupported_task() -> None:
    result = parse_agent_pr_comment("/agent-pr arbitrary_task ./aaa.txt")

    assert result.valid is False
    assert "Unsupported task_id" in (result.error_message or "")


def test_parse_rejects_wrong_arity() -> None:
    result = parse_agent_pr_comment("/agent-pr append_hello_agent_comment")

    assert result.valid is False
    assert "Expected exactly two arguments" in (result.error_message or "")


def test_write_output_github_format(tmp_path: Path) -> None:
    output_file = tmp_path / "gh_output.txt"
    result = parse_agent_pr_comment("/agent-pr append_hello_agent_comment ./aaa.txt")

    _write_output(output_file, result, OutputFormat.GITHUB)

    assert output_file.read_text(encoding="utf-8") == (
        "valid=true\ntask_id=append_hello_agent_comment\ntarget_file=aaa.txt\nerror_message=\n"
    )


def test_write_output_dotenv_format(tmp_path: Path) -> None:
    output_file = tmp_path / "agent.env"
    result = parse_agent_pr_comment("/agent-pr arbitrary_task ./aaa.txt")

    _write_output(output_file, result, OutputFormat.DOTENV)

    text = output_file.read_text(encoding="utf-8")
    assert "VALID=false\n" in text
    assert "TASK_ID=\n" in text
    assert "TARGET_FILE=\n" in text
    assert "ERROR_MESSAGE=Unsupported task_id" in text
