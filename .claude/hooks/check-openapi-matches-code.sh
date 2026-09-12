#!/usr/bin/env bash
# Se dispara antes de "git commit" (ver .claude/settings.json, hook PreToolUse).
# Bloquea el commit si openapi.json no coincide con lo que genera el código
# ahora mismo, usando el comando de regeneración de README.md.
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

TMP_SPEC="$(mktemp)"
trap 'rm -f "$TMP_SPEC"' EXIT

# DATABASE_URL no siempre está exportado en el entorno que ejecuta el hook.
# app.openapi() no abre conexión: basta con un valor con la forma correcta,
# y el de abajo es el mismo valor ficticio de .env.example (nunca el de .env).
if ! DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://app_user:app_password@localhost:5432/app_db}" \
    timeout 10 uv run python -c "
import json
from app.main import app
json.dump(app.openapi(), open('$TMP_SPEC', 'w'), indent=2, ensure_ascii=False)
" > /tmp/openapi-hook.log 2>&1
then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"No se pudo regenerar la especificación OpenAPI para compararla con openapi.json (detalle en /tmp/openapi-hook.log). No se bloqueó por una diferencia real, sino porque la comprobación no corrió: revisa el entorno (uv sync, DATABASE_URL) y repetí el commit."}}
EOF
  exit 0
fi

if ! diff -q "$TMP_SPEC" openapi.json > /dev/null 2>&1; then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"openapi.json no coincide con la especificación que genera el código actual. Regeneralo con el comando de README.md (sección OpenAPI): uv run python -c \"import json; from app.main import app; json.dump(app.openapi(), open('openapi.json', 'w'), indent=2, ensure_ascii=False)\" — agregalo al commit con git add openapi.json y repetí el commit."}}
EOF
  exit 0
fi

exit 0
