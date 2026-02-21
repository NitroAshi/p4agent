from __future__ import annotations

import argparse
import json
import shlex
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from core.settings import settings
from tasks.registry import TaskRegistry

AGENT_PR_PREFIX = "/agent-pr"


class OutputFormat(StrEnum):
    GITHUB = "github"
    DOTENV = "dotenv"


@dataclass(frozen=True)
class AgentPrCommand:
    task_id: str
    payload_json: str


@dataclass(frozen=True)
class ParseResult:
    valid: bool
    command: AgentPrCommand | None
    error_message: str | None


def parse_agent_pr_comment(
    comment_body: str,
    *,
    supported_task_ids: set[str] | None = None,
) -> ParseResult:
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
            error_message="Missing arguments. Expected: /agent-pr <task_id> '<json_payload>'",
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
            error_message="Expected exactly two arguments: /agent-pr <task_id> '<json_payload>'",
        )

    task_id, payload_json = parts
    known_task_ids = supported_task_ids or set(TaskRegistry(settings.task_config_dir).list_ids())
    if task_id not in known_task_ids:
        known = ", ".join(sorted(known_task_ids))
        return ParseResult(
            valid=False,
            command=None,
            error_message=f"Unsupported task_id '{task_id}'. Supported tasks: {known}",
        )

    try:
        payload_obj = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        return ParseResult(
            valid=False,
            command=None,
            error_message=f"Payload must be valid JSON object: {exc}",
        )

    if not isinstance(payload_obj, dict):
        return ParseResult(
            valid=False,
            command=None,
            error_message="Payload must decode to a JSON object.",
        )

    normalized_payload = json.dumps(payload_obj, ensure_ascii=True, separators=(",", ":"))
    return ParseResult(
        valid=True,
        command=AgentPrCommand(task_id=task_id, payload_json=normalized_payload),
        error_message=None,
    )


def _format_output_lines(result: ParseResult, output_format: OutputFormat) -> list[str]:
    key_map = (
        {
            "valid": "valid",
            "task_id": "task_id",
            "payload_json": "payload_json",
            "error_message": "error_message",
        }
        if output_format == OutputFormat.GITHUB
        else {
            "valid": "VALID",
            "task_id": "TASK_ID",
            "payload_json": "PAYLOAD_JSON",
            "error_message": "ERROR_MESSAGE",
        }
    )

    if result.valid and result.command is not None:
        return [
            f"{key_map['valid']}=true",
            f"{key_map['task_id']}={result.command.task_id}",
            f"{key_map['payload_json']}={result.command.payload_json}",
            f"{key_map['error_message']}=",
        ]

    message = result.error_message or "Unknown parse error"
    return [
        f"{key_map['valid']}=false",
        f"{key_map['task_id']}=",
        f"{key_map['payload_json']}=",
        f"{key_map['error_message']}={message}",
    ]


def _write_output(path: Path, result: ParseResult, output_format: OutputFormat) -> None:
    if output_format not in {OutputFormat.GITHUB, OutputFormat.DOTENV}:
        raise ValueError(f"Unsupported output format: {output_format}")

    with path.open("a", encoding="utf-8") as file_obj:
        for line in _format_output_lines(result, output_format):
            file_obj.write(f"{line}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse /agent-pr command body")
    parser.add_argument("--comment", required=True, help="Issue comment body")
    parser.add_argument(
        "--output-file",
        required=True,
        help="Output file path (for GitHub output file or GitLab dotenv artifact)",
    )
    parser.add_argument(
        "--output-format",
        choices=[OutputFormat.GITHUB.value, OutputFormat.DOTENV.value],
        default=OutputFormat.GITHUB.value,
        help="Output format for CI integration",
    )
    args = parser.parse_args()

    result = parse_agent_pr_comment(args.comment)
    _write_output(
        path=Path(args.output_file),
        result=result,
        output_format=OutputFormat(args.output_format),
    )


if __name__ == "__main__":
    main()
