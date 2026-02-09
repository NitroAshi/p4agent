#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${AGENT_ISSUE_IID:-}" || -z "${GITLAB_TOKEN:-}" ]]; then
  echo "Skip issue note: AGENT_ISSUE_IID or GITLAB_TOKEN is missing."
  exit 0
fi

body="$(cat)"

curl --fail --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --data-urlencode "body=${body}" \
  "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/issues/${AGENT_ISSUE_IID}/notes"
