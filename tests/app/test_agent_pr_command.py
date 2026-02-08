from app.agent_pr_command import parse_agent_pr_comment


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
