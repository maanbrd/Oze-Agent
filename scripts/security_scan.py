#!/usr/bin/env python3
"""Lightweight local security preflight for Agent-OZE.

The scan intentionally avoids printing secret values. It checks tracked files
for common live-secret markers and inventories local env files by path/size only.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SECRET_PATTERNS = [
    re.compile(r"sk_live_[A-Za-z0-9]{16,}"),
    re.compile(r"whsec_[A-Za-z0-9]{16,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    re.compile(r"(?m)^(?:TELEGRAM_BOT_TOKEN|OPENAI_API_KEY|ANTHROPIC_API_KEY|GOOGLE_CLIENT_SECRET|SUPABASE_SERVICE_KEY|ENCRYPTION_KEY)=\S+"),
]

IGNORED_TRACKED_SUFFIXES = {
    "package-lock.json",
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return [
        ROOT / item.decode()
        for item in result.stdout.split(b"\0")
        if item
    ]


def env_files() -> list[Path]:
    ignored_names = {".env.example"}
    results: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.name in ignored_names:
            continue
        if path.name == ".env" or path.name.startswith(".env."):
            results.append(path)
    return sorted(results)


def scan_tracked() -> list[str]:
    findings: list[str] = []
    for path in tracked_files():
        relative = path.relative_to(ROOT)
        if str(relative).endswith(tuple(IGNORED_TRACKED_SUFFIXES)):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"{relative}: secret-looking value matched {pattern.pattern[:24]}...")
    return findings


def main() -> int:
    findings = scan_tracked()
    if findings:
        print("Tracked secret scan failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("Tracked secret scan OK")
    local_envs = env_files()
    if local_envs:
        print("Local env files present (values not printed):")
        for path in local_envs:
            size = os.path.getsize(path)
            print(f"- {path.relative_to(ROOT)} ({size} bytes)")
    else:
        print("No local env files found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
