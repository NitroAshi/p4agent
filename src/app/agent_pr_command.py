from __future__ import annotations

import argparse
import shlex
from dataclasses import dataclass
from pathlib import Path

AGENT_PR_PREFIX = "/agent-pr"
SUPPORTED_TASK_IDS = {"append_hello_agent_comment"}


@dataclass(frozen=True)
class AgentPrCommand:
    task_id: str
    target_file: str


@dataclass(frozen=True)
class ParseResult:
    valid: bool
    command: AgentPrCommand | None
    error_message: str | None


def parse_agent_pr_comment(comment_body: str) -> ParseResult:
    text = comment_body.strip()
    if not text.startswith(AGENT_PR_PREFIX):
        return ParseResult(
            valid=False,
            command=None,
            error_message=f"Command must start with '{AGENT_PR_PREFIX}'.",
        )

    command_tail = text[len(AGENT_PR_PREFIX) :].strip()
    if not command_tail:
        return ParseResult(
            valid=False,
            command=None,
            error_message="Missing arguments. Expected: /agent-pr <task_id> <target_file>",
        )

    try:
        parts = shlex.split(command_tail)
    except ValueError as exc:
        return ParseResult(
            valid=False,
            command=None,
            error_message=f"Unable to parse command arguments: {exc}",
        )

    if len(parts) != 2:
        return ParseResult(
            valid=False,
            command=None,
            error_message="Expected exactly two arguments: /agent-pr <task_id> <target_file>",
        )

    task_id, target_file = parts
    if task_id not in SUPPORTED_TASK_IDS:
        known = ", ".join(sorted(SUPPORTED_TASK_IDS))
        return ParseResult(
            valid=False,
            command=None,
            error_message=f"Unsupported task_id '{task_id}'. Supported tasks: {known}",
        )

    normalized_target = str(Path(target_file))
    return ParseResult(
        valid=True,
        command=AgentPrCommand(task_id=task_id, target_file=normalized_target),
        error_message=None,
    )


def _write_output(path: Path, result: ParseResult) -> None:
    with path.open("a", encoding="utf-8") as file_obj:
        if result.valid and result.command is not None:
            file_obj.write("valid=true\n")
            file_obj.write(f"task_id={result.command.task_id}\n")
            file_obj.write(f"target_file={result.command.target_file}\n")
            file_obj.write("error_message=\n")
            return

        message = result.error_message or "Unknown parse error"
        file_obj.write("valid=false\n")
        file_obj.write("task_id=\n")
        file_obj.write("target_file=\n")
        file_obj.write(f"error_message={message}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse /agent-pr command body")
    parser.add_argument("--comment", required=True, help="Issue comment body")
    parser.add_argument(
        "--output-file",
        required=True,
        help="GitHub output file path (typically $GITHUB_OUTPUT)",
    )
    args = parser.parse_args()

    result = parse_agent_pr_comment(args.comment)
    _write_output(path=Path(args.output_file), result=result)


if __name__ == "__main__":
    main()
