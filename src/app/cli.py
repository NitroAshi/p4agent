import argparse
import json
from typing import Any

from core.service import AgentService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run p4agent demo tasks")
    parser.add_argument("--task-id", required=True, help="Task identifier from configs/tasks")
    parser.add_argument(
        "--input-json",
        required=True,
        help="Raw JSON payload object for the task",
    )
    return parser.parse_args()


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    loaded = json.loads(args.input_json)
    if not isinstance(loaded, dict):
        raise ValueError("--input-json must decode to a JSON object")
    return loaded


def main() -> None:
    args = parse_args()
    payload = build_payload(args)
    service = AgentService()
    result = service.run_task(task_id=args.task_id, payload=payload)
    print(json.dumps(result, ensure_ascii=True, indent=2))
