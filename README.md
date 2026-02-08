# p4agent-demo

A LangChain + LangGraph demo framework in Python for PR-driven agent development.

## What this demo includes

- `src/core`: Runtime state and orchestration.
- `src/tasks`: Task contracts and task registry.
- `src/infra`: File-system tooling and external adapters.
- `src/app`: API and CLI entrypoints.
- `configs/tasks`: Machine-readable task specs.
- `docs/tasks`: Human-readable task definitions.
- `tests`: Unit and integration tests for core flows.
- `.github`: CI plus PR/Issue templates.

## Quick start

```bash
uv sync --all-extras
uv run pytest
uv run p4agent-cli --task-id append_hello_agent_comment --target-file ./README.md
uv run p4agent-api
```

## LLM provider configuration

Set runtime variables in `.env` (or CI secrets):

```bash
P4AGENT_LLM_ENABLED=false
P4AGENT_LLM_PROVIDER=openai # openai | anthropic | azure
P4AGENT_LLM_MODEL=gpt-4o-mini
P4AGENT_LLM_FALLBACK_TO_RULES=true

OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=...
```

## Demo task

`append_hello_agent_comment` appends `# hello from p4agent` to the end of a Python file.

## PR workflow

- Open branch from `main` (`feat/*`, `fix/*`).
- Ensure lint/type/test checks pass.
- Fill PR template with risk and rollback notes.
- Request review.

## First automated AI PR (issue comment trigger)

This repo includes a GitHub Action workflow: `.github/workflows/agent-pr.yml`.

Current scope:

- Trigger by issue comment command.
- Run one approved task only: `append_hello_agent_comment`.
- Create draft PR after checks pass.

Trigger example:

```text
/agent-pr append_hello_agent_comment ./aaa.txt
```

Full guide:

- `docs/first_ai_pr.md`
