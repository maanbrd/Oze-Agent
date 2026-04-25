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
if [[ -x ".venv/bin/python" ]]; then
    exec ".venv/bin/python" -m tests_e2e.mcp_server "$@"
else
    exec python3 -m tests_e2e.mcp_server "$@"
fi
