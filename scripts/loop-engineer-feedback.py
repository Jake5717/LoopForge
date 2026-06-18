#!/usr/bin/env python3
"""Feedback ingestion for Loop Engineer.
Adds items to the dynamic backlog from various sources.

Configuration (environment variables):
  LOOPFORGE_DATA_DIR   — Data directory (default: ~/.loopforge)
  LOOPFORGE_OWNER      — Owner name (default: "owner")

Usage:
  python3 loop-engineer-feedback.py --feedback "script.py gave wrong alert about X"
  python3 loop-engineer-feedback.py --incident /path/to/incident.md
  python3 loop-engineer-feedback.py --verifier "script.py missing cross-host correlation"
  python3 loop-engineer-feedback.py --system "Improver prompt is too vague about selection"
"""

import argparse
import os
import re
from datetime import datetime

DATA_DIR = os.environ.get("LOOPFORGE_DATA_DIR", os.path.expanduser("~/.loopforge"))
BACKLOG_PATH = os.path.join(DATA_DIR, "data", "loop-engineer", "backlog.md")
OWNER = os.environ.get("LOOPFORGE_OWNER", "owner")

# Map script/job names to backlog sections
JOB_MAP = {
    "ic-containers.py": "Job 1: ic-containers.py",
    "ic-resources.py": "Job 2: ic-resources.py",
    "ic-errors.py": "Job 3: ic-errors.py",
    "network-guard.py": "Job 4: network-guard.py",
    "network-guard": "Job 5: Network Guard Analysis",
    "ic-morning": "Job 6: IC Morning Briefing",
    "morning-briefing": "Job 6: IC Morning Briefing",
    "ward": "Job 7: Ward",
    "scribe": "Job 8: Scribe",
    "linkedin": "Job 9: LinkedIn Monitor",
    "discord": "Job 10: Discord Thread Renamer",
    "hermes-news": "Job 11: Hermes & AI News",
    "guyana": "Job 12: Guyana News",
    "git-backup": "Job 13: Git Backup",
    "loop-engineer": "Job 14: Loop Engineer (Self-Improvement)",
}


def find_job_section(text):
    """Try to match a job section from the feedback text."""
    text_lower = text.lower()
    for key, section in JOB_MAP.items():
        if key in text_lower:
            return section
    return None


def add_to_backlog(section, item, source):
    """Add an item to the backlog under the specified section."""
    today = datetime.now().strftime("%Y-%m-%d")
    new_line = f"- [ ] {item} — [source: {source}] — {today}\n"

    with open(BACKLOG_PATH, "r") as f:
        content = f.read()

    # Find the section and add after "_No items yet._" or after last item
    pattern = f"(## {re.escape(section)}\n)_No items yet\._\n"
    if re.search(pattern, content):
        content = re.sub(pattern, f"\\1{new_line}", content)
    else:
        # Find the section header and append before next ## or end
        header = f"## {section}"
        idx = content.find(header)
        if idx == -1:
            print(f"Section '{section}' not found in backlog")
            return False
        # Find next section or end
        next_section = content.find("\n## ", idx + len(header))
        if next_section == -1:
            content = content.rstrip() + "\n" + new_line
        else:
            content = content[:next_section] + new_line + content[next_section:]

    with open(BACKLOG_PATH, "w") as f:
        f.write(content)

    print(f"Added to {section}: {item}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Ingest feedback into Loop Engineer backlog")
    parser.add_argument("--feedback", help="Owner's feedback about a script/job")
    parser.add_argument("--incident", help="Path to incident file to extract context from")
    parser.add_argument("--verifier", help="Verifier finding about a script/job")
    parser.add_argument("--system", help="System-level improvement finding")
    args = parser.parse_args()

    if args.feedback:
        section = find_job_section(args.feedback) or "Job 14: Loop Engineer (Self-Improvement)"
        add_to_backlog(section, args.feedback, OWNER)
    elif args.incident:
        if os.path.exists(args.incident):
            with open(args.incident) as f:
                content = f.read()
            # Try to extract which job is relevant from incident content
            section = find_job_section(content) or "Job 14: Loop Engineer (Self-Improvement)"
            title = content.split("\n")[0].replace("#", "").strip()[:100]
            add_to_backlog(section, f"Incident: {title}", "incident")
        else:
            print(f"Incident file not found: {args.incident}")
    elif args.verifier:
        section = find_job_section(args.verifier) or "Job 14: Loop Engineer (Self-Improvement)"
        add_to_backlog(section, args.verifier, "verifier")
    elif args.system:
        add_to_backlog("Job 14: Loop Engineer (Self-Improvement)", args.system, "system")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
