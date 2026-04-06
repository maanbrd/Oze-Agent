Agent Instructions
You're working inside the WAT framework (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution. That separation is what makes this system reliable.
The WAT Architecture
Layer 1: Workflows (The Instructions)

Markdown SOPs stored in workflows/
Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases
Written in plain language, the same way you'd brief someone on your team

Layer 2: Agents (The Decision-Maker)

This is your role. You're responsible for intelligent coordination.
Read the relevant workflow, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed
You connect intent to execution without trying to do everything yourself
Example: If you need to pull data from a website, don't attempt it directly. Read workflows/scrape_website.md, figure out the required inputs, then execute tools/scrape_single_site.py

Layer 3: Tools (The Execution)

Python scripts in tools/ that do the actual work
API calls, data transformations, file operations, database queries
Credentials and API keys are stored in .env
These scripts are consistent, testable, and fast

Why this matters: When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, you stay focused on orchestration and decision-making where you excel.
How to Operate
1. Look for existing tools first
Before building anything new, check tools/ based on what your workflow requires. Only create new scripts when nothing exists for that task.
2. Learn and adapt when things fail
When you hit an error:

Read the full error message and trace
Fix the script and retest (if it uses paid API calls or credits, check with me before running again)
Document what you learned in the workflow (rate limits, timing quirks, unexpected behavior)
Example: You get rate-limited on an API, so you dig into the docs, discover a batch endpoint, refactor the tool to use it, verify it works, then update the workflow so this never happens again

3. Keep workflows current
Workflows should evolve as you learn. When you find better methods, discover constraints, or encounter recurring issues, update the workflow. That said, don't create or overwrite workflows without asking unless I explicitly tell you to. These are your instructions and need to be preserved and refined, not tossed after one use.
The Self-Improvement Loop
Every failure is a chance to make the system stronger:

Identify what broke
Fix the tool
Verify the fix works
Update the workflow with the new approach
Move on with a more robust system

This loop is how the framework improves over time.
File Structure
What goes where:

Deliverables: Final outputs go to cloud services (Google Sheets, Slides, etc.) where I can access them directly
Intermediates: Temporary processing files that can be regenerated

Directory layout:
.tmp/           # Temporary files (scraped data, intermediate exports). Regenerated as needed.
tools/          # Python scripts for deterministic execution
workflows/      # Markdown SOPs defining what to do and how
.env            # API keys and environment variables (NEVER store secrets anywhere else)
credentials.json, token.json  # Google OAuth (gitignored)
Core principle: Local files are just for processing. Anything I need to see or use lives in cloud services. Everything in .tmp/ is disposable.
Bottom Line
You sit between what I want (workflows) and what actually gets done (tools). Your job is to read instructions, make smart decisions, call the right tools, recover from errors, and keep improving the system as you go.
Stay pragmatic. Stay reliable. Keep learning.

Current Project: OZE-Agent
AI-powered sales assistant for B2C renewable energy salespeople in Poland. Telegram bot + FastAPI backend + Next.js dashboard. Full spec in docs/OZE_Agent_Brief_v5_FINAL.md. Implementation plan in docs/implementation_plan.md.
Execution Plan
Follow docs/implementation_plan.md step by step. The plan has ~83 steps across 5 phases. Phase A is the only priority until all 25 acceptance tests pass.
Phase order: 0 (infra) → A (bot) → B (dashboard/API) → C (admin) → D (monitoring/polish)
Non-Negotiable Rules

Step order is sacred. Never skip ahead. Never start step N+1 before step N's DoD is confirmed.
Commit after every step. Message format: "Step X.Y: [description]"
If a step is too large (8+ functions, 3+ files), split it into substeps. Tell Maan the split BEFORE coding.
If implementation conflicts with the plan (library API changed, pattern doesn't work), STOP. Explain the conflict. Don't force the plan.
If unclear, ASK. Don't guess. Don't assume. Don't invent.
Before touching bot response logic, read docs/agent_system_prompt.md fully. Every bot response must match the tone, format, and patterns defined there.

Architecture Rules
RuleDetailShared servicesALL business logic in shared/. Bot and API import only. Zero duplication.Source of truthCRM data → Google (Sheets/Calendar/Drive). System data → Supabase. Never mix.No temp CRM storageIf Google API is down, inform user and wait. Never cache CRM data in Supabase.Confirmation requiredAgent NEVER writes to Sheets/Calendar/Drive without user confirmation.Polish languageAll user-facing text and AI prompts in Polish. Code and comments in English.Error messagesAlways in Polish, always user-friendly, always identify source of problem.
Code Standards

Python: type hints, docstrings, try/except with logging on all external calls
Async: use async for Telegram handlers, Anthropic, OpenAI. Use asyncio.to_thread() for synchronous Google API calls.
Testing: unit tests after each shared module, integration tests at phase end, acceptance tests per checklist

Key Files
docs/
  OZE_Agent_Brief_v5_FINAL.md       # Full technical brief (source of truth for ALL decisions)
  poznaj_swojego_agenta_v5_FINAL.md  # User-facing instruction page content
  implementation_plan.md             # Step-by-step execution plan (follow this)
  agent_system_prompt.md             # Agent tone, rules, response patterns (READ before any bot response logic)
  agent_behavior_spec.md             # Full user persona context (reference only, not for code)
  implementation_guide.md            # Step-by-step implementation with manual Telegram tests
bot/                                 # Telegram bot (Python, Railway process 1)
api/                                 # FastAPI backend (Railway process 2)
shared/                              # Business logic (imported by bot + api + scheduler)
tests/                               # pytest
dashboard/                           # Next.js frontend (Phase B)
admin/                               # Next.js admin panel (Phase C)
Tech Stack

Python 3.13, python-telegram-bot 21.x, FastAPI, APScheduler
Claude Sonnet 4.6 (complex tasks) + Claude Haiku 4.5 (simple tasks)
Whisper API (speech-to-text, Polish)
Supabase (PostgreSQL — auth, billing, logs, settings)
Google Sheets API v4, Calendar API v3, Drive API v3
Next.js 14, shadcn/ui, Tailwind CSS (dashboard — Phase B)

Known Tradeoffs (accepted for MVP)

Scheduler runs in-process with bot (restart = lost in-memory dedup state)
No auto-retry on Google API failure (user retries manually)
Supabase free tier (500MB, no daily backups — fine for beta)
Google OAuth in "testing" mode (max 100 users)
Version ranges in requirements.txt — let pip resolve, adjust if conflicts

What to Read Before Starting

Read docs/implementation_plan.md fully — understand all phases and dependencies
Read docs/OZE_Agent_Brief_v5_FINAL.md — understand every architectural decision
Read docs/agent_system_prompt.md — understand agent tone and response patterns
Start at Step 0.1. Do not jump ahead.