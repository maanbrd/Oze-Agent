# Claude Agent SDK — developer setup

Claude Code SDK is now named **Claude Agent SDK**.

This repo uses it only as a local developer tool. It is not part of the
Telegram bot, FastAPI backend, Railway runtime, or Vercel web runtime.

## Install

```bash
cd /Users/mansoniasty/workflows/Agent-OZE
python3 -m pip install -r requirements-dev.txt
npm install -g @anthropic-ai/claude-code
claude login
```

Do not put `ANTHROPIC_API_KEY` or Claude credentials in the repository. If you
use API-key auth instead of `claude login`, export it only in your shell.

## Usage

Read-only planning mode:

```bash
python3 scripts/claude_repo_agent.py "Inspect this repo and summarize the next safest implementation step."
```

Prompt from file:

```bash
python3 scripts/claude_repo_agent.py --prompt-file docs/PLAN_FIX_E2E_SUPABASE_MAPPING.md
```

Allow file edits:

```bash
python3 scripts/claude_repo_agent.py --mode acceptEdits "Implement the approved plan, but do not commit."
```

## Defaults

- working directory: repo root
- project instructions: `CLAUDE.md` / project settings via `setting_sources=["project"]`
- permission mode: `plan`
- max turns: `8`
- max budget: `$2.00`

Use `--help` to see runtime options.
