#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${GITLAB_TOKEN:-}" ]]; then
  echo "GITLAB_TOKEN is required."
  exit 1
fi

if [[ -z "${TASK_ID:-}" || -z "${TARGET_FILE:-}" ]]; then
  echo "TASK_ID and TARGET_FILE are required."
  exit 1
fi

branch_name="codex/issue-${AGENT_ISSUE_IID:-manual}-${CI_PIPELINE_ID}"

git config user.name "p4agent-bot"
git config user.email "p4agent-bot@example.com"
git checkout -B "${branch_name}"
git add -A

if git diff --cached --quiet; then
  printf "MR_URL=\nBRANCH_NAME=%s\n" "${branch_name}" > mr.env
  exit 0
fi

git commit -m "feat(agent): run ${TASK_ID} on ${TARGET_FILE}"

remote_url="https://oauth2:${GITLAB_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git"
git push "${remote_url}" "HEAD:${branch_name}"

description="$(
  cat <<EOF
## Summary
- Triggered by AGENT_COMMAND in GitLab CI.
- Task: \`${TASK_ID}\`
- Target: \`${TARGET_FILE}\`

## Validation
- [x] \`uv run ruff format --check .\`
- [x] \`uv run ruff check .\`
- [x] \`uv run mypy src tests\`
- [x] \`uv run pytest\`

## Source
- Pipeline: ${CI_PIPELINE_URL}
EOF
)"

response="$(curl --fail --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --data-urlencode "source_branch=${branch_name}" \
  --data-urlencode "target_branch=${CI_DEFAULT_BRANCH}" \
  --data-urlencode "title=Draft: agent: ${TASK_ID} for #${AGENT_ISSUE_IID:-manual}" \
  --data-urlencode "remove_source_branch=true" \
  --data-urlencode "description=${description}" \
  "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/merge_requests")"

mr_url="$(printf '%s' "${response}" | python3 -c 'import json,sys; data=json.loads(sys.stdin.read()); print(data.get("web_url",""))')"
printf "MR_URL=%s\nBRANCH_NAME=%s\n" "${mr_url}" "${branch_name}" > mr.env
