#!/usr/bin/env python3
"""Create a daily report markdown file."""

from __future__ import annotations

import argparse
import os
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo


DATE_PATTERN = re.compile(r"^\d{4}/\d{2}/\d{2}\.md$")
TOTAL_PATTERN = re.compile(r"-\s*Total:\s*([0-9,]+(?:\.\d+)?)h")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a daily report markdown file.")
    parser.add_argument("--date", default="", help="Report date in YYYY-MM-DD. Defaults to today in Asia/Tokyo.")
    parser.add_argument("--topics", required=True, help="Learning topics. Use new lines for multiple bullets.")
    parser.add_argument("--hours", required=True, help="Today's learning hours, e.g. 1.5")
    parser.add_argument("--memo", default="", help="Free-form learning memo. Defaults to 特になし.")
    parser.add_argument("--dry-run", action="store_true", help="Print the generated report without writing a file.")
    return parser.parse_args()


def parse_report_date(value: str) -> datetime:
    if value:
        return datetime.strptime(value, "%Y-%m-%d")
    return datetime.now(ZoneInfo("Asia/Tokyo"))


def parse_hours(value: str) -> Decimal:
    try:
        hours = Decimal(value)
    except InvalidOperation as exc:
        raise SystemExit(f"Invalid --hours value: {value}") from exc

    if hours < 0:
        raise SystemExit("--hours must be zero or greater.")
    return hours


def format_hours(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.1"))
    return f"{rounded:,.1f}"


def report_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.glob("[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9].md")
        if DATE_PATTERN.match(path.relative_to(root).as_posix())
    )


def extract_total(path: Path) -> Decimal:
    content = path.read_text(encoding="utf-8")
    match = TOTAL_PATTERN.search(content)
    if not match:
        raise SystemExit(f"Could not find Total in previous report: {path}")
    return Decimal(match.group(1).replace(",", ""))


def previous_report(root: Path, target_path: Path) -> Path | None:
    target_key = target_path.relative_to(root).as_posix()
    candidates = [
        path
        for path in report_files(root)
        if path.relative_to(root).as_posix() < target_key
    ]
    return candidates[-1] if candidates else None


def topic_lines(value: str) -> list[str]:
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    if not lines:
        raise SystemExit("--topics must not be empty.")

    return [line[2:].strip() if line.startswith("- ") else line for line in lines]


def build_report(topics: list[str], today_hours: Decimal, total_hours: Decimal, memo: str) -> str:
    topic_markdown = "\n".join(f"- {topic}" for topic in topics)
    memo_markdown = memo.strip() or "特になし"
    return (
        "## 学習内容\n"
        f"{topic_markdown}\n\n"
        "## 学習時間\n"
        f"- Today: {format_hours(today_hours)}h\n"
        f"- Total: {format_hours(total_hours)}h\n\n"
        "## 学習メモ\n"
        f"{memo_markdown}\n"
    )


def write_github_output(values: dict[str, str]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return

    with Path(output_path).open("a", encoding="utf-8") as output:
        for key, value in values.items():
            output.write(f"{key}={value}\n")


def main() -> None:
    args = parse_args()
    root = Path.cwd()
    report_date = parse_report_date(args.date)
    target_path = root / f"{report_date:%Y}" / f"{report_date:%m}" / f"{report_date:%d}.md"

    if target_path.exists() and not args.dry_run:
        raise SystemExit(f"Report already exists: {target_path}")

    today_hours = parse_hours(args.hours)
    previous_path = previous_report(root, target_path)
    previous_total = extract_total(previous_path) if previous_path else Decimal("0")
    new_total = previous_total + today_hours
    content = build_report(topic_lines(args.topics), today_hours, new_total, args.memo)
    commit_message = f"{report_date:%Y%m%d}の日報作成"

    if args.dry_run:
        print(content, end="")
    else:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

    write_github_output(
        {
            "report_path": target_path.relative_to(root).as_posix(),
            "previous_report": previous_path.relative_to(root).as_posix() if previous_path else "",
            "previous_total": format_hours(previous_total),
            "new_total": format_hours(new_total),
            "commit_message": commit_message,
        }
    )

    print(f"report_path={target_path.relative_to(root).as_posix()}")
    print(f"previous_total={format_hours(previous_total)}")
    print(f"new_total={format_hours(new_total)}")
    print(f"commit_message={commit_message}")


if __name__ == "__main__":
    main()
