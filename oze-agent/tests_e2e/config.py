"""E2E harness configuration loaded from environment variables.

All values are loaded from environment (see tests_e2e/.env.example for the
expected set). A missing required variable raises RuntimeError with a
pointer to README.md.
"""

import os
from dataclasses import dataclass
from pathlib import Path


_REPO_E2E_DIR = Path(__file__).resolve().parent


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"E2E config: required env var {name!r} is not set. "
            f"See {_REPO_E2E_DIR}/README.md for setup."
        )
    return value


def _require_int(name: str) -> int:
    raw = _require(name)
    try:
        return int(raw)
    except ValueError as e:
        raise RuntimeError(f"E2E config: {name} must be an integer, got {raw!r}") from e


@dataclass
class E2EConfig:
    """Read-only snapshot of E2E harness configuration."""

    # Telethon credentials — obtained at https://my.telegram.org/apps
    api_id: int
    api_hash: str

    # Session file path for the test user account. After first interactive
    # login (phone + OTP), Telethon persists auth here — subsequent runs
    # are non-interactive.
    session_path: str

    # Bot to interact with. Accepts @username or numeric id.
    bot_username: str

    # Expected admin id that the bot accepts for /debug_brief etc. The
    # test user MUST match this id on the target bot (prod or staging).
    admin_telegram_id: int

    # Where the PASS/FAIL report is written.
    report_path: str

    @classmethod
    def from_env(cls) -> "E2EConfig":
        return cls(
            api_id=_require_int("TELEGRAM_E2E_API_ID"),
            api_hash=_require("TELEGRAM_E2E_API_HASH"),
            session_path=os.getenv(
                "TELEGRAM_E2E_SESSION",
                str(_REPO_E2E_DIR / ".sessions" / "e2e"),
            ),
            bot_username=_require("TELEGRAM_E2E_BOT_USERNAME"),
            admin_telegram_id=_require_int("TELEGRAM_E2E_ADMIN_ID"),
            report_path=os.getenv(
                "TELEGRAM_E2E_REPORT",
                str(Path.cwd() / "test_results_e2e.md"),
            ),
        )
