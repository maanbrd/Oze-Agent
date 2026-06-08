#!/usr/bin/env bash
# Release-gate command wrapper. Keeps generated commands short while still
# loading the E2E env and preferring the project venv when available.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OZE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$OZE_DIR"

if [[ -f "tests_e2e/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "tests_e2e/.env"
    set +a
fi

PY=".venv/bin/python"
if [[ ! -x "$PY" ]]; then
    if command -v pytest >/dev/null 2>&1; then
        pytest_path="$(command -v pytest)"
        pytest_shebang="$(head -n 1 "$pytest_path" 2>/dev/null || true)"
        if [[ "$pytest_shebang" == '#!'* ]]; then
            candidate="${pytest_shebang#'#!'}"
            if [[ -x "$candidate" ]]; then
                PY="$candidate"
            else
                PY="python3"
            fi
        else
            PY="python3"
        fi
    else
        PY="python3"
    fi
fi

cmd="${1:-}"
if [[ -z "$cmd" ]]; then
    exec "$PY" -m tests_e2e.release_gate
fi
if [[ "$cmd" == --* ]]; then
    exec "$PY" -m tests_e2e.release_gate "$@"
fi
shift || true

case "$cmd" in
    pytest-tests)
        exec "$PY" -m pytest tests_e2e/tests -q "$@"
        ;;
    list)
        exec "$PY" -m tests_e2e.runner --list "$@"
        ;;
    google-health)
        exec "$PY" -m tests_e2e.google_health "$@"
        ;;
    seed)
        exec "$PY" -m tests_e2e.fixtures seed "$@"
        ;;
    cleanup)
        exec "$PY" -m tests_e2e.fixtures cleanup "$@"
        ;;
    category)
        category="${1:-}"
        if [[ -z "$category" ]]; then
            echo "usage: $0 category <name> [runner args...]" >&2
            exit 2
        fi
        shift
        exec "$PY" -m tests_e2e.runner --category "$category" "$@"
        ;;
    *)
        echo "unknown release-gate command: $cmd" >&2
        exit 2
        ;;
esac
