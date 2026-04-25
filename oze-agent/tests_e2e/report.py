"""PASS/FAIL result types + markdown report writer for the E2E harness.

The report file is human-readable and small by design. Each scenario run
appends a section with its checks and any observed messages.

Tag system (Phase 7A):
  pass          — OK (default)
  fail          — new regression, blocks PASS
  known_drift   — known divergence from docs (logged separately, does not block)
  expected_fail — scenario tests POST-MVP behaviour, fail is expected, no block
  blocker       — infrastructure broken (auth, no bot reply); aborts suite

A scenario PASSes when every check is in {pass, known_drift, expected_fail}
and there is no `blocker`. Any `fail` flips the scenario to FAIL.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

# Stable, validated tag set. Order matters for severity sorting.
Tag = Literal["pass", "known_drift", "expected_fail", "fail", "blocker"]
_VALID_TAGS: tuple[Tag, ...] = (
    "pass", "known_drift", "expected_fail", "fail", "blocker",
)
_NON_BLOCKING: frozenset[Tag] = frozenset({"pass", "known_drift", "expected_fail"})


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""
    tag: Tag = "pass"
    # Optional doc reference for known_drift / expected_fail
    doc_ref: str = ""

    def __post_init__(self) -> None:
        if self.tag not in _VALID_TAGS:
            raise ValueError(f"invalid tag: {self.tag!r}")
        # Auto-derive: passed=False with default tag should become "fail".
        if not self.passed and self.tag == "pass":
            self.tag = "fail"


@dataclass
class ScenarioResult:
    scenario_name: str
    started_at: datetime
    ended_at: datetime | None = None
    checks: list[CheckResult] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    category: str = ""

    @property
    def passed(self) -> bool:
        if not self.checks:
            return False
        return all(c.tag in _NON_BLOCKING for c in self.checks)

    @property
    def has_blocker(self) -> bool:
        return any(c.tag == "blocker" for c in self.checks)

    def add(
        self,
        name: str,
        ok: bool,
        detail: str = "",
        *,
        tag: Tag | None = None,
        doc_ref: str = "",
    ) -> None:
        """Append a check. If tag is omitted, derived from `ok`
        (True → pass, False → fail). Caller may override e.g.
        with tag="known_drift" to flag a docs/code divergence
        that should not block the suite."""
        if tag is None:
            tag = "pass" if ok else "fail"
        self.checks.append(CheckResult(name, ok, detail, tag=tag, doc_ref=doc_ref))

    def add_known_drift(self, name: str, detail: str, doc_ref: str = "") -> None:
        """Helper for known docs↔code drifts (e.g. card label wording)."""
        self.checks.append(
            CheckResult(name, False, detail, tag="known_drift", doc_ref=doc_ref)
        )

    def add_blocker(self, name: str, detail: str) -> None:
        """Helper for infrastructure failures that abort the suite."""
        self.checks.append(CheckResult(name, False, detail, tag="blocker"))

    def verdict(self) -> str:
        if self.has_blocker:
            return "BLOCKER"
        return "PASS" if self.passed else "FAIL"


# ── Markdown rendering ────────────────────────────────────────────────────────


_TAG_ICON: dict[Tag, str] = {
    "pass": "✅",
    "known_drift": "⚠️",
    "expected_fail": "🟡",
    "fail": "❌",
    "blocker": "🛑",
}


def _format_section(r: ScenarioResult) -> str:
    lines: list[str] = []
    verdict = r.verdict()
    if r.has_blocker:
        icon = "🛑"
    elif r.passed:
        icon = "✅"
    else:
        icon = "❌"
    cat_suffix = f"  _[{r.category}]_" if r.category else ""
    lines.append(f"## {icon} `{r.scenario_name}` — {verdict}{cat_suffix}")
    lines.append("")
    lines.append(f"- started: `{r.started_at.isoformat()}`")
    if r.ended_at:
        duration = (r.ended_at - r.started_at).total_seconds()
        lines.append(f"- ended:   `{r.ended_at.isoformat()}` ({duration:.1f}s)")
    lines.append("")
    lines.append("| Check | Tag | Detail |")
    lines.append("|---|---|---|")
    for c in r.checks:
        mark = _TAG_ICON.get(c.tag, "?")
        detail = c.detail.replace("|", "\\|").replace("\n", " ↵ ")
        if c.doc_ref:
            detail = f"{detail} — _ref: {c.doc_ref}_"
        lines.append(f"| `{c.name}` | {mark} `{c.tag}` | {detail} |")
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


def _summary_counts(results: list[ScenarioResult]) -> dict[Tag, int]:
    """Count checks by tag across all scenarios."""
    counts: dict[Tag, int] = {t: 0 for t in _VALID_TAGS}
    for r in results:
        for c in r.checks:
            counts[c.tag] += 1
    return counts


def write_report(results: list[ScenarioResult], path: str) -> None:
    """Write a human-readable markdown report of all scenario runs.

    Overwrites the target file each time. Suite passes only if every
    scenario's `passed` is True (i.e. no `fail` or `blocker` checks).
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    has_blocker = any(r.has_blocker for r in results)
    overall_pass = bool(results) and not has_blocker and all(r.passed for r in results)

    if has_blocker:
        header_icon = "🛑"
        verdict_text = "BLOCKER"
    elif overall_pass:
        header_icon = "✅"
        verdict_text = "PASS"
    else:
        header_icon = "❌"
        verdict_text = "FAIL"

    now = datetime.now(tz=timezone.utc).isoformat()
    counts = _summary_counts(results)
    pass_count = sum(1 for r in results if r.passed)
    blocker_count = sum(1 for r in results if r.has_blocker)

    sections = [f"# OZE-Agent E2E Report {header_icon}", ""]
    sections.append(f"_Generated: {now}_")
    sections.append("")
    sections.append(f"**Overall:** {verdict_text}")
    sections.append(f"**Scenarios:** {len(results)} (pass {pass_count}, "
                    f"blocker {blocker_count})")
    sections.append("")
    sections.append("**Check tag counts:** "
                    + ", ".join(f"{_TAG_ICON[t]} {t}={counts[t]}" for t in _VALID_TAGS))
    sections.append("")

    # Group sections by tag severity for quicker scanning.
    blockers = [r for r in results if r.has_blocker]
    fails = [r for r in results if not r.has_blocker and not r.passed]
    drifts = [
        r for r in results
        if r.passed and any(c.tag == "known_drift" for c in r.checks)
    ]
    cleans = [
        r for r in results
        if r.passed and not any(c.tag == "known_drift" for c in r.checks)
    ]

    if blockers:
        sections.append("## 🛑 Blockers")
        sections.append("")
        for r in blockers:
            sections.append(_format_section(r))
        sections.append("---")
        sections.append("")
    if fails:
        sections.append("## ❌ Fails")
        sections.append("")
        for r in fails:
            sections.append(_format_section(r))
        sections.append("---")
        sections.append("")
    if drifts:
        sections.append("## ⚠️ Known drifts (PASS but log)")
        sections.append("")
        for r in drifts:
            sections.append(_format_section(r))
        sections.append("---")
        sections.append("")
    if cleans:
        sections.append("## ✅ Clean PASS")
        sections.append("")
        for r in cleans:
            sections.append(_format_section(r))
        sections.append("---")
        sections.append("")

    p.write_text("\n".join(sections), encoding="utf-8")
