#!/usr/bin/env bash
# Wrapper for Claude Code MCP registration. Handles cwd, env loading, and
# venv resolution so the MCP config stays 1-liner and free of secrets.
set -euo pipefail

# Resolve to the repo's oze-agent/ directory regardless of how the script
# is invoked (symlink, absolute path, etc.).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OZE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$OZE_DIR"

# Load tests_e2e/.env into the environment. The MCP server reads these
# at startup. Keep secrets in .env (gitignored), not in Claude Code config.
if [[ -f "tests_e2e/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "tests_e2e/.env"
    set +a
fi

# Prefer the project venv's Python (3.13, matches prod runtime). Fall back
# to system python3 if the venv is not present.
PY=".venv/bin/python"
[[ -x "$PY" ]] || PY="python3"

# Wrap with `railway run` so the MCP server inherits Supabase env
# (SUPABASE_URL, SUPABASE_SERVICE_KEY, GOOGLE_*, etc.) from Railway prod.
# Per CLAUDE.md (Phase 0.8 cleanup): production secrets live ONLY in
# Railway env vars — not in tests_e2e/.env, which keeps only Telethon
# credentials (TELEGRAM_E2E_*).
exec railway run --service bot --environment production -- \
    "$PY" -m tests_e2e.mcp_server "$@"
