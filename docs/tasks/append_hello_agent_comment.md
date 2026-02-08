# Task: append_hello_agent_comment

## Goal

Append `# hello from p4agent` to the end of a target Python file.

## Input

- `target_file` (string): absolute or project-relative path to the file.

## Output

- `status`: `ok` or `failed`
- `task_id`: task identifier
- `changed_file`: path that was modified
- `appended_text`: appended content

## Constraints

- Single tool call only.
- No overwrite behavior, append-only.
- Create file if target does not exist.
