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
- `.github`: GitHub CI plus PR/Issue templates.
- `.gitlab-ci.yml`: GitLab CI for quality gates plus automated MR creation.

## Quick start

```bash
uv sync --all-extras
uv run pytest
uv run p4agent-cli --task-id append_hello_agent_comment --input-json '{"target_file":"./README.md"}'
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

CI notes:

- GitHub Actions can inject OpenAI config via one combined secret `GLM_ENV` (multiline `KEY=value`) or by setting `OPENAI_API_KEY` and `OPENAI_BASE_URL` directly.
- GitLab CI should set `OPENAI_API_KEY` and `OPENAI_BASE_URL` directly in CI/CD variables.

## Demo task

`append_hello_agent_comment` appends `# hello from p4agent` to the end of a Python file.

## Daily Hacker News pipeline task

Run the multilingual daily report pipeline:

```bash
PLAYWRIGHT_BROWSERS_PATH=.playwright-browsers uv run playwright install chromium
uv run p4agent-cli --task-id daily_google_news_report_pipeline --input-json '{"max_items":10,"timezone":"Asia/Shanghai","output_path":"artifacts/news_today.md"}'
```

You can skip `PLAYWRIGHT_BROWSERS_PATH` if browsers are already installed globally.

If your provider times out or rate-limits, tune translation batching/retries:

```bash
uv run p4agent-cli --task-id daily_google_news_report_pipeline --input-json '{"max_items":10,"timezone":"Asia/Shanghai","output_path":"artifacts/news_today.md","translate_batch_size":2,"translate_max_retries":4,"translate_retry_seconds":2}'
```

## PR workflow

- Open branch from `main` (`feat/*`, `fix/*`).
- Ensure lint/type/test checks pass.
- Fill PR template with risk and rollback notes.
- Request review.

## CI support matrix

- GitHub: push/PR quality checks in `.github/workflows/ci.yml`.
- GitLab: push/MR quality checks in `.gitlab-ci.yml` (`quality` job).
- GitHub agent command: issue comment trigger creates Draft PR.
- GitLab agent command: pipeline variable trigger creates Draft MR and can reply to issue notes.

## First automated AI PR (GitHub issue comment trigger)

This repo includes a GitHub Action workflow: `.github/workflows/agent-pr.yml`.

Current scope:

- Trigger by issue comment command.
- Run one approved task only: `append_hello_agent_comment`.
- Create draft PR after checks pass.

Trigger example:

```text
/agent-pr append_hello_agent_comment '{"target_file":"./aaa.txt"}'
```

Full guide:

- `docs/first_ai_pr.md`

## First automated AI MR (GitLab pipeline trigger)

This repo also includes a GitLab pipeline: `.gitlab-ci.yml`.

Current scope:

- Trigger by starting a pipeline and passing `AGENT_COMMAND`.
- Run one approved task only: `append_hello_agent_comment`.
- Create draft MR after checks pass.

Trigger variables example:

```text
AGENT_COMMAND=/agent-pr append_hello_agent_comment '{"target_file":"./aaa.txt"}'
AGENT_ISSUE_IID=123
```

Mode options:

- `AGENT_MODE=fast` (default): only parse + run task, publish task output artifact.
- `AGENT_MODE=full`: parse + run + quality checks + detect changes + create Draft MR.

Full guide:

- `docs/first_ai_mr_gitlab.md`
