# p4agent-demo

A LangChain + LangGraph demo framework in Python for PR-driven agent development.

## What this demo includes

- `src/agent_core`: Task registry, state machine, and tool execution.
- `src/app`: API and CLI entrypoints.
- `configs/tasks`: Machine-readable task specs.
- `docs/tasks`: Human-readable task definitions.
- `tests`: Unit and integration tests for core flows.
- `.github`: CI plus PR/Issue templates.

## Quick start

```bash
uv sync --all-extras
uv run pytest
uv run p4agent-cli --task-id append_hello_agnet_comment --target-file ./README.md
uv run p4agent-api
```

## Demo task

`append_hello_agnet_comment` appends `# hello agnet` to the end of a Python file.

## PR workflow

- Open branch from `main` (`feat/*`, `fix/*`).
- Ensure lint/type/test checks pass.
- Fill PR template with risk and rollback notes.
- Request review.
