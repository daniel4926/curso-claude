#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c 'import json, sys; print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))')

if echo "$COMMAND" | grep -qE '^uv run pytest( |$)' \
  || echo "$COMMAND" | grep -qE '^uv run ruff check( |$)' \
  || echo "$COMMAND" | grep -qE '^curl (http://localhost|http://127\.0\.0\.1)' \
  || echo "$COMMAND" | grep -qE '^git (status|diff|log|ls-files|show|check-ignore)( |$)'; then
  exit 0
fi

echo "Bloqueado: consolidador-de-hallazgos solo puede correr pytest -k, ruff check, peticiones a localhost, o git de solo lectura." >&2
exit 2
