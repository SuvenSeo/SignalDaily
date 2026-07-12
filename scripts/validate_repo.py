#!/usr/bin/env python3
"""SignalDaily repository validator.

This script intentionally uses only the Python standard library so it can run in
GitHub Actions without dependency installation.
"""
from __future__ import annotations

import re
from pathlib import Path

REQUIRED_ROOT_FILES = [
    "README.md",
    "AGENT.md",
    "PROMPTS.md",
    "OPERATIONS.md",
    "DISCLAIMER.md",
    "SECURITY.md",
]

REQUIRED_TEMPLATES = [
    "templates/daily-brief.md",
    "templates/lightweight-update.md",
    "templates/telegram-alert-template.md",
]

REQUIRED_DAILY_SECTIONS = [
    "## Executive Summary",
    "## AI & Models",
    "## Coding & Developer Tools",
    "## Sri Lanka / CSE / Economy",
    "## Global Markets",
    "## Opportunity Radar",
    "## Deep Dive of the Day",
    "## Watchlist for Tomorrow",
    "## Sources",
]

DATE_RE = re.compile(r"^daily/(20\d{2})-(0\d|1[0-2])-([0-2]\d|3[01])\.md$")
DANGEROUS_FINANCIAL_LANGUAGE = re.compile(
    r"\b(guaranteed returns?|risk-free profit|must buy|must sell|sure win|100% profit)\b",
    re.IGNORECASE,
)


def fail(message: str) -> None:
    print(f"ERROR: {message}")


def warn(message: str) -> None:
    print(f"WARN: {message}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_required_files(root: Path) -> int:
    errors = 0
    for rel in REQUIRED_ROOT_FILES + REQUIRED_TEMPLATES:
        if not (root / rel).is_file():
            fail(f"Missing required file: {rel}")
            errors += 1
    return errors


def check_daily_file(path: Path, root: Path) -> int:
    errors = 0
    rel = path.relative_to(root).as_posix()
    match = DATE_RE.match(rel)
    if not match:
        fail(f"Daily brief path must be daily/YYYY-MM-DD.md: {rel}")
        return 1

    date = rel.removeprefix("daily/").removesuffix(".md")
    text = read(path)

    if f"# SignalDaily Intelligence Brief — {date}" not in text:
        fail(f"{rel}: title must include exact date {date}")
        errors += 1

    for section in REQUIRED_DAILY_SECTIONS:
        if section not in text:
            fail(f"{rel}: missing required section: {section}")
            errors += 1

    if "## Sources" in text:
        sources = text.split("## Sources", 1)[1]
        source_lines = [line for line in sources.splitlines() if line.strip().startswith("-")]
        if len(source_lines) < 5:
            warn(f"{rel}: fewer than 5 source bullets detected")

    if DANGEROUS_FINANCIAL_LANGUAGE.search(text):
        fail(f"{rel}: contains unsafe financial-advice wording")
        errors += 1

    if "not financial advice" not in text.lower() and "no financial advice" not in text.lower():
        warn(f"{rel}: no explicit financial-advice disclaimer detected")

    return errors


def check_markdown_hygiene(root: Path) -> int:
    errors = 0
    for path in root.rglob("*.md"):
        rel = path.relative_to(root).as_posix()
        text = read(path)
        if "TODO" in text and not rel.startswith("ideas/"):
            warn(f"{rel}: TODO marker remains")
        if "\t" in text:
            warn(f"{rel}: tab character found; prefer spaces")
        if text and not text.endswith("\n"):
            fail(f"{rel}: file must end with a newline")
            errors += 1
    return errors


def main() -> int:
    root = Path.cwd()
    errors = 0
    errors += check_required_files(root)
    errors += check_markdown_hygiene(root)

    daily_dir = root / "daily"
    if daily_dir.exists():
        for path in sorted(daily_dir.glob("*.md")):
            errors += check_daily_file(path, root)

    if errors:
        print(f"\nSignalDaily validation failed with {errors} error(s).")
        return 1

    print("SignalDaily validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
