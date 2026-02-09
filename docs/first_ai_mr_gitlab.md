# First AI MR Guide (GitLab)

This guide shows the exact steps to trigger your first automated AI MR in this repo.

## What this automation can do now

- It can run one approved task: `append_hello_agent_comment`.
- It cannot run arbitrary coding instructions yet.
- It creates a draft MR only when the task changes files and all checks pass.
- It can post issue notes for invalid command, no-change result, MR link, and execution failure.

## One-time setup

1. Push this repository to GitLab.
2. Ensure GitLab CI/CD is enabled for the repository.
3. Ensure the default branch is `main`.
4. Add CI/CD variable `GITLAB_TOKEN` (recommended: Project Access Token with `api` + `write_repository`).
5. Optional: add LLM secrets if you want external model output.
   - Set `OPENAI_API_KEY` and `OPENAI_BASE_URL` directly in GitLab CI/CD variables.

This workflow also works without external LLM secrets because fallback mode is enabled.

## Trigger pipeline

Run a new pipeline and provide variables:

```text
AGENT_COMMAND=/agent-pr append_hello_agent_comment ./aaa.txt
AGENT_ISSUE_IID=123
```

`AGENT_ISSUE_IID` is optional. If present, the pipeline posts status notes back to the issue.

Optional mode variable:

```text
AGENT_MODE=fast   # default, only parse + run task
AGENT_MODE=full   # includes quality checks and Draft MR creation
```

## Command format

```text
/agent-pr <task_id> <target_file>
```

Rules:

- `task_id` must be `append_hello_agent_comment`
- `target_file` can be relative path like `./aaa.txt`
- For paths with spaces, use quotes:

```text
/agent-pr append_hello_agent_comment "./notes/demo file.py"
```

## What the bot does after trigger

1. Parses your command.
2. Runs the task via `p4agent-cli`.
3. Runs quality checks:
   - `uv run ruff format --check .`
   - `uv run ruff check .`
   - `uv run mypy src tests`
   - `uv run pytest`
4. Creates a draft MR if checks pass and changes exist.
5. Optionally replies in issue notes with parse errors, no-change status, or MR link.
6. On failure after successful parse, optionally replies with pipeline URL.

When `AGENT_MODE=fast`, the workflow stops after task execution and publishes task output artifacts.

## Naming and response conventions

- Branch: `codex/issue-<issue_iid_or_manual>-<pipeline_id>`
- MR title: `Draft: agent: <task_id> for #<issue_iid_or_manual>`
- Commit message: `feat(agent): run <task_id> on <target_file>`
- Invalid command reply:
  - starts with `I could not parse this command.`
  - includes reason and valid command example
- No-change reply:
  - starts with `Task ran successfully, but no file changes were detected.`

## Safe usage recommendations

- Use one issue per requested change.
- Keep target file scoped and explicit.
- Review every draft MR before marking ready and merging.
- Keep branch protection on `main`.
