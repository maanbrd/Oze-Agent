"""PASS/FAIL result types + markdown report writer for the E2E harness.

The report file is human-readable and small by design. Each scenario run
appends a section with its checks and any observed messages.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class ScenarioResult:
    scenario_name: str
    started_at: datetime
    ended_at: datetime | None = None
    checks: list[CheckResult] = field(default_factory=list)
    # Free-form context for debugging: observed message texts, counts, etc.
    context: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(c.passed for c in self.checks)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(CheckResult(name, ok, detail))

    def verdict(self) -> str:
        return "PASS" if self.passed else "FAIL"


def _format_section(r: ScenarioResult) -> str:
    lines: list[str] = []
    verdict = r.verdict()
    icon = "✅" if r.passed else "❌"
    lines.append(f"## {icon} {r.scenario_name} — {verdict}")
    lines.append("")
    lines.append(f"- started: `{r.started_at.isoformat()}`")
    if r.ended_at:
        duration = (r.ended_at - r.started_at).total_seconds()
        lines.append(f"- ended:   `{r.ended_at.isoformat()}` ({duration:.1f}s)")
    lines.append("")
    lines.append("| Check | Result | Detail |")
    lines.append("|---|---|---|")
    for c in r.checks:
        mark = "✅" if c.passed else "❌"
        detail = c.detail.replace("|", "\\|").replace("\n", " ↵ ")
        lines.append(f"| `{c.name}` | {mark} | {detail} |")
    if r.context:
        lines.append("")
        lines.append("<details><summary>Context</summary>")
        lines.append("")
        lines.append("```")
        for k, v in r.context.items():
            lines.append(f"{k}: {v!r}")
        lines.append("```")
        lines.append("</details>")
    lines.append("")
    return "\n".join(lines)


def write_report(results: list[ScenarioResult], path: str) -> None:
    """Write a human-readable markdown report of all scenario runs.

    Overwrites the target file each time (the intent is to inspect the
    latest run). Includes overall PASS/FAIL at the top.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    overall_pass = bool(results) and all(r.passed for r in results)
    header_icon = "✅" if overall_pass else "❌"
    now = datetime.now(tz=timezone.utc).isoformat()

    sections = [f"# OZE-Agent E2E Report {header_icon}", ""]
    sections.append(f"_Generated: {now}_")
    sections.append("")
    sections.append(f"**Overall:** {'PASS' if overall_pass else 'FAIL'}")
    sections.append(f"**Scenarios:** {len(results)}")
    pass_count = sum(1 for r in results if r.passed)
    sections.append(f"**Passed:** {pass_count} / {len(results)}")
    sections.append("")
    sections.append("---")
    sections.append("")
    for r in results:
        sections.append(_format_section(r))
        sections.append("---")
        sections.append("")
    p.write_text("\n".join(sections), encoding="utf-8")
