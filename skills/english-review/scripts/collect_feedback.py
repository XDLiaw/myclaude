"""Collect English feedback blocks from recent Claude Code session transcripts.

Scans ~/.claude/projects/*/*.jsonl for assistant messages containing an
"English feedback" header, pairs each with the user message that triggered it
(via parentUuid walk), and writes a markdown practice file.

Usage:
    python collect_feedback.py [--days N] [--output PATH] [--project NAME]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECTS_ROOT = Path.home() / ".claude" / "projects"
DEFAULT_OUTPUT_DIR = Path.home() / ".claude" / "skills" / "english-review" / "exercises"

FEEDBACK_HEADER_RE = re.compile(
    r"(?:#{1,6}[^\n]*?English\s+Feedback|\*\*English feedback[^*]*\*\*)",
    re.IGNORECASE,
)
# Section terminator: horizontal rule (---), heavy unicode line (━━━), or similar separator.
SECTION_END_RE = re.compile(r"^\s*(?:-{3,}|━{3,}|═{3,})\s*$", re.MULTILINE)


@dataclass
class FeedbackItem:
    timestamp: str
    session_id: str
    user_message: str
    feedback_block: str


def iter_session_files(project_filter: str | None):
    if not PROJECTS_ROOT.exists():
        return
    for project_dir in PROJECTS_ROOT.iterdir():
        if not project_dir.is_dir():
            continue
        if project_filter and project_filter not in project_dir.name:
            continue
        for jsonl in project_dir.glob("*.jsonl"):
            yield jsonl


def load_session(path: Path) -> list[dict]:
    entries = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return entries


def extract_text_from_assistant(entry: dict) -> str:
    """Join all text parts from an assistant message."""
    msg = entry.get("message", {})
    content = msg.get("content", [])
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for c in content:
        if isinstance(c, dict) and c.get("type") == "text":
            parts.append(c.get("text", ""))
    return "\n".join(parts)


def extract_text_from_user(entry: dict) -> str:
    """Get the user's message text, skipping tool results and system reminders."""
    msg = entry.get("message", {})
    content = msg.get("content", [])
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for c in content:
        if not isinstance(c, dict):
            continue
        # Skip tool_result entries — those aren't Eric's prose.
        if c.get("type") == "text":
            parts.append(c.get("text", ""))
    return "\n".join(parts).strip()


def find_feedback_block(text: str) -> str | None:
    """Return the feedback block starting at the 'English feedback' header."""
    match = FEEDBACK_HEADER_RE.search(text)
    if not match:
        return None
    start = match.start()
    tail = text[start:]
    # End the block at the first horizontal rule that follows (commonly separates feedback from task response).
    end_match = SECTION_END_RE.search(tail, pos=10)  # skip the header itself
    if end_match:
        return tail[: end_match.start()].strip()
    return tail.strip()


def walk_back_to_user(entries_by_uuid: dict, start_uuid: str) -> str:
    """Follow parentUuid chain from the assistant entry back to the nearest user text."""
    current = entries_by_uuid.get(start_uuid)
    hops = 0
    while current and hops < 20:
        parent_uuid = current.get("parentUuid")
        if not parent_uuid:
            return ""
        parent = entries_by_uuid.get(parent_uuid)
        if not parent:
            return ""
        if parent.get("type") == "user":
            text = extract_text_from_user(parent)
            # Skip empty or obviously system-generated user entries.
            if text and not text.startswith("<system-reminder>"):
                return text
        current = parent
        hops += 1
    return ""


def within_window(ts_str: str, cutoff: datetime) -> bool:
    try:
        # Python < 3.11 dislikes trailing "Z" — replace with +00:00.
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except ValueError:
        return False
    return ts >= cutoff


def collect(days: int, project_filter: str | None) -> list[FeedbackItem]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items: list[FeedbackItem] = []
    seen_keys: set[tuple[str, str]] = set()

    for session_path in iter_session_files(project_filter):
        entries = load_session(session_path)
        if not entries:
            continue
        entries_by_uuid = {e.get("uuid"): e for e in entries if e.get("uuid")}

        for entry in entries:
            if entry.get("type") != "assistant":
                continue
            ts = entry.get("timestamp", "")
            if not within_window(ts, cutoff):
                continue
            text = extract_text_from_assistant(entry)
            block = find_feedback_block(text)
            if not block:
                continue
            user_msg = walk_back_to_user(entries_by_uuid, entry.get("uuid", ""))
            if not user_msg:
                continue
            key = (user_msg[:80], block[:80])
            if key in seen_keys:
                continue
            seen_keys.add(key)
            items.append(
                FeedbackItem(
                    timestamp=ts,
                    session_id=entry.get("sessionId", session_path.stem),
                    user_message=user_msg,
                    feedback_block=block,
                )
            )

    items.sort(key=lambda i: i.timestamp)
    return items


def render_markdown(items: list[FeedbackItem], days: int) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    if not items:
        return f"# English Review — {today}\n\nNo English feedback found in the last {days} day(s). Nothing to review today.\n"

    lines = [f"# English Review — {today}", ""]
    lines.append(f"Collected from {len({i.session_id for i in items})} session(s). {len(items)} feedback item(s).")
    lines.append("")

    for idx, item in enumerate(items, 1):
        user_preview = item.user_message.strip().splitlines()[0][:200] if item.user_message else "(no user message found)"
        lines.append(f"## Item {idx}")
        lines.append("")
        lines.append("**Context (what you were asking):**")
        lines.append(f"> {user_preview}")
        lines.append("")
        lines.append("**Feedback Claude gave you:**")
        lines.append("")
        # Indent the feedback block into a blockquote-style section, preserving its markdown.
        for fb_line in item.feedback_block.splitlines():
            lines.append(fb_line)
        lines.append("")
        lines.append("**Practice — rewrite this correctly (in your head, or write below):**")
        lines.append(f"> {user_preview}")
        lines.append("")
        lines.append("_Your answer:_ ")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total items: {len(items)}")
    lines.append("- Look for repeated patterns (prepositions, articles, verb tense, word choice).")
    lines.append("- Pick your top 2 weak patterns and practice those tomorrow.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=1, help="How many past days to scan (default: 1).")
    parser.add_argument("--output", type=Path, default=None, help="Output markdown path.")
    parser.add_argument("--project", type=str, default=None, help="Substring filter for project directory name.")
    args = parser.parse_args()

    items = collect(args.days, args.project)

    today = datetime.now().strftime("%Y-%m-%d")
    output_path = args.output or (DEFAULT_OUTPUT_DIR / f"{today}.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    markdown = render_markdown(items, args.days)
    output_path.write_text(markdown, encoding="utf-8")

    print(f"Wrote {len(items)} feedback item(s) to: {output_path}")
    if not items:
        print("(No feedback found in scan window.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
