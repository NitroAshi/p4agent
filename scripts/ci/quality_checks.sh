#!/usr/bin/env bash
set -euo pipefail

with_coverage="${1:-}"

uv run ruff format --check .
uv run ruff check .
uv run mypy src tests

if [[ "$with_coverage" == "--with-coverage" ]]; then
  uv run pytest --cov --cov-report=xml
  exit 0
fi

uv run pytest
