# First AI PR Guide

This guide shows the exact steps to trigger your first automated AI PR in this repo.

## What this automation can do now

- It can run one approved task: `append_hello_agent_comment`.
- It cannot run arbitrary coding instructions yet.
- It creates a draft PR only when the task changes files and all checks pass.

## One-time setup

1. Push this repository to GitHub.
2. Ensure GitHub Actions are enabled for the repository.
3. Ensure the default branch is `main`.
4. Optional: add LLM secrets if you want external model output.
   - Option A: set one multiline secret `GLM_ENV` with lines like `OPENAI_API_KEY=...` and `OPENAI_BASE_URL=...`.
   - Option B: set `OPENAI_API_KEY` and `OPENAI_BASE_URL` as separate GitHub secrets.

This workflow also works without external LLM secrets because fallback mode is enabled.

## Trigger command

Create a GitHub issue, then add this comment:

```text
/agent-pr append_hello_agent_comment ./aaa.txt
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

1. Parses your comment command.
2. Runs the task via `p4agent-cli`.
3. Runs quality checks:
   - `uv run ruff check .`
   - `uv run mypy src tests`
   - `uv run pytest`
4. Creates a draft PR if checks pass and changes exist.
5. Replies in the issue with the PR link.

## Naming and response conventions

- Branch: `codex/issue-<issue_number>-<run_id>`
- PR title: `agent: <task_id> for #<issue_number>`
- Commit message: `feat(agent): run <task_id> on <target_file>`
- Invalid command reply:
  - starts with `I could not parse this command.`
  - includes reason and valid command example
- No-change reply:
  - starts with `Task ran successfully, but no file changes were detected.`

## Safe usage recommendations

- Use one issue per requested change.
- Keep target file scoped and explicit.
- Review every draft PR before marking ready and merging.
- Keep branch protection on `main`.

## Next step to support more AI tasks

To add a second task, you need three changes:

1. Add a new task YAML in `configs/tasks/`.
2. Add execution mapping in `src/core/orchestrator.py`.
3. Add tests, then allow the new `task_id` in `src/app/agent_pr_command.py`.
