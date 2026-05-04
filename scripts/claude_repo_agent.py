#!/usr/bin/env python3
"""Run Claude Agent SDK against this repository as a developer tool.

The default mode is read-only planning. Use --mode acceptEdits only when you
intend to let Claude edit files.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

SYSTEM_APPEND = """\
You are working on OZE-Agent.

Before proposing or changing code, follow this repository's CLAUDE.md and
AGENTS.md instructions. In particular:
- read docs/SOURCE_OF_TRUTH.md and docs/CURRENT_STATUS.md first;
- do not use docs/archive/ as current implementation guidance;
- do not commit unless Maan explicitly asks;
- do not store secrets in the repository.
"""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a one-off Claude Agent SDK task in this repo."
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Prompt text. If omitted, use --prompt-file or stdin.",
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Read prompt from a file instead of command-line text/stdin.",
    )
    parser.add_argument(
        "--mode",
        choices=("plan", "default", "acceptEdits"),
        default="plan",
        help="Claude permission mode. Default: plan (read-only).",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("CLAUDE_AGENT_MODEL"),
        help="Claude model name/alias. Defaults to SDK/CLI default.",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=8,
        help="Maximum agent tool-use turns. Default: 8.",
    )
    parser.add_argument(
        "--budget-usd",
        type=float,
        default=2.0,
        help="Maximum SDK session budget in USD. Default: 2.0.",
    )
    return parser.parse_args()


def _load_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return args.prompt_file.read_text(encoding="utf-8").strip()
    if args.prompt:
        return " ".join(args.prompt).strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    raise SystemExit("Provide a prompt, --prompt-file, or stdin.")


def _text_from_content_block(block: Any) -> str | None:
    if isinstance(block, dict):
        return block.get("text")
    return getattr(block, "text", None)


def _print_message(message: Any) -> None:
    content = getattr(message, "content", None)
    if isinstance(content, list):
        for block in content:
            text = _text_from_content_block(block)
            if text:
                print(text, end="" if text.endswith("\n") else "\n")
        return

    result = getattr(message, "result", None)
    if isinstance(result, str) and result:
        print(result, end="" if result.endswith("\n") else "\n")


async def _run() -> int:
    args = _parse_args()
    prompt = _load_prompt(args)

    try:
        from claude_agent_sdk import (  # type: ignore[import-not-found]
            CLIJSONDecodeError,
            CLINotFoundError,
            ClaudeAgentOptions,
            ProcessError,
            query,
        )
    except ModuleNotFoundError:
        print(
            "Missing claude-agent-sdk. Install dev dependencies with:\n"
            "  python3 -m pip install -r requirements-dev.txt",
            file=sys.stderr,
        )
        return 2

    options = ClaudeAgentOptions(
        cwd=REPO_ROOT,
        tools={"type": "preset", "preset": "claude_code"},
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": SYSTEM_APPEND,
        },
        setting_sources=["project"],
        permission_mode=args.mode,
        max_turns=args.max_turns,
        max_budget_usd=args.budget_usd,
        model=args.model,
    )

    try:
        async for message in query(prompt=prompt, options=options):
            _print_message(message)
    except CLINotFoundError:
        print(
            "Claude Code CLI not found. Install/login first:\n"
            "  npm install -g @anthropic-ai/claude-code\n"
            "  claude login",
            file=sys.stderr,
        )
        return 2
    except ProcessError as exc:
        print(f"Claude process failed with exit code {exc.exit_code}.", file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        return exc.exit_code or 1
    except CLIJSONDecodeError as exc:
        print(f"Claude SDK failed to parse CLI output: {exc}", file=sys.stderr)
        return 1

    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
