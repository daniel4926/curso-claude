#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c 'import json, sys; print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))')

if echo "$COMMAND" | grep -qE '^uv run pytest( |$)' \
  || echo "$COMMAND" | grep -qE '^uv run ruff check( |$)'; then
  exit 0
fi

echo "Bloqueado: refactorizador solo puede correr 'uv run pytest' o 'uv run ruff check'." >&2
exit 2
