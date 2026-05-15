#!/usr/bin/env bash
set -u -o pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/app/frontend"
EXIT_CODE=0

# Read hook payload to keep compatibility with PostToolUse hooks.
INPUT="$(cat)"
FILE_PATH="$(echo "$INPUT" | python3 -c "
import json, sys
try:
    payload = json.load(sys.stdin)
    print(payload.get('tool_input', {}).get('file_path', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")"

log_step() {
  printf "\n[post_file_edit] %s\n" "$1"
}

run_step() {
  local name="$1"
  shift
  log_step "$name"
  if ! "$@"; then
    EXIT_CODE=1
  fi
}

install_frontend_dependencies() {
  if (cd "${FRONTEND_DIR}" && npm ci); then
    return
  fi

  echo "[post_file_edit] Warning: npm ci failed, falling back to npm install."
  (cd "${FRONTEND_DIR}" && npm install --package-lock=false --no-audit --no-fund)
}

run_frontend_checks() {
  if [[ ! -d "${FRONTEND_DIR}" ]]; then
    echo "[post_file_edit] Frontend directory missing, skipping frontend checks."
    return
  fi

  run_step "Frontend: install dependencies" install_frontend_dependencies
  run_step "Frontend: lint" bash -lc "cd \"${FRONTEND_DIR}\" && npm run lint"
  run_step "Frontend: typecheck" bash -lc "cd \"${FRONTEND_DIR}\" && npm run typecheck"
  run_step "Frontend: next build" bash -lc "cd \"${FRONTEND_DIR}\" && NEXT_PUBLIC_API_URL=\"http://localhost:8000/api/v1\" NEXT_PUBLIC_SITE_URL=\"http://localhost:3000\" NEXT_PUBLIC_SUPABASE_URL=\"https://example.supabase.co\" NEXT_PUBLIC_SUPABASE_ANON_KEY=\"sb_publishable_ci_dummy_key\" npm run build"
  run_step "Frontend: format check" bash -lc "cd \"${FRONTEND_DIR}\" && npm run format:check"
  run_step "Frontend: tests" bash -lc "cd \"${FRONTEND_DIR}\" && npm run test"
}

run_python_checks() {
  run_step "Python: sync dev dependencies" bash -lc "cd \"${ROOT_DIR}\" && uv sync --extra dev"
  run_step "Python: Ruff lint" bash -lc "cd \"${ROOT_DIR}\" && uv run ruff check ."
  run_step "Python: BasedPyright type check" bash -lc "cd \"${ROOT_DIR}\" && uv run basedpyright --level error ."

  if [[ -d "${ROOT_DIR}/tests" ]]; then
    run_step "Python: pytest" bash -lc "cd \"${ROOT_DIR}\" && uv run pytest -q"
  else
    log_step "Python: pytest skipped (no tests directory)"
  fi

  run_step "Python: compile smoke check" bash -lc "cd \"${ROOT_DIR}\" && uv run python -m compileall -x app/frontend app"
}

log_step "Triggered by file edit: ${FILE_PATH:-unknown}"
run_frontend_checks
run_python_checks

if [[ "${EXIT_CODE}" -ne 0 ]]; then
  echo "[post_file_edit] One or more checks failed."
else
  echo "[post_file_edit] All checks passed."
fi

# Keep post-edit hook non-blocking while still surfacing failures in output.
exit 0
