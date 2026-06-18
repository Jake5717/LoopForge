#!/usr/bin/env python3
"""
Approval Processor — Runs on schedule to:
1. Expire old proposals
2. Process approved proposals
3. Output a digest of pending items (for the agent to deliver to the owner)

This script is designed to be run by a cron job. It outputs structured
JSON that the agent can use to send notifications.

Configuration (environment variables):
  LOOPFORGE_DATA_DIR   — Data directory (default: ~/.loopforge)
  LOOPFORGE_OWNER      — Owner name for approvals (default: "owner")
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(os.environ.get("LOOPFORGE_DATA_DIR", os.path.expanduser("~/.loopforge")))
APPROVALS_DIR = BASE_DIR / "approvals"
PENDING_DIR = APPROVALS_DIR / "pending"
APPROVED_DIR = APPROVALS_DIR / "approved"

OWNER = os.environ.get("LOOPFORGE_OWNER", "owner")

def run_manager(*args):
    """Run the approval-manager.py script and return output."""
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "approval-manager.py")
    cmd = [sys.executable, script] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode

def check_expired():
    """Check for and expire old proposals."""
    output, code = run_manager("check-expired")
    return output

def process_approved():
    """Process approved proposals."""
    # First check if there are any approved
    approved_files = list(APPROVED_DIR.glob("apr-*.json"))
    if not approved_files:
        return None

    # Process them (not dry-run)
    output, code = run_manager("process")
    return output

def get_pending():
    """Get list of pending proposals."""
    pending_files = list(PENDING_DIR.glob("apr-*.json"))
    pending = []
    for f in sorted(pending_files):
        with open(f) as fh:
            pending.append(json.load(fh))
    return pending

def generate_digest():
    """Generate a digest of pending items."""
    output, code = run_manager("digest")
    return output

def main():
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "expired": None,
        "processed": None,
        "pending_count": 0,
        "pending_items": [],
        "digest": None,
    }

    # Step 1: Expire old proposals
    expired_output = check_expired()
    if expired_output and "Expired:" in expired_output:
        results["expired"] = expired_output

    # Step 2: Process approved proposals
    processed_output = process_approved()
    if processed_output:
        results["processed"] = processed_output

    # Step 3: Check pending items
    pending = get_pending()
    results["pending_count"] = len(pending)
    results["pending_items"] = [
        {
            "id": p["id"],
            "title": p["title"],
            "risk": p["risk"],
            "type": p["type"],
            "security_sensitive": p.get("security_sensitive", False),
            "expires": p.get("expires"),
        }
        for p in pending
    ]

    # Step 4: Generate digest if there are pending items
    if pending:
        results["digest"] = generate_digest()

    # Output structured result
    print(json.dumps(results, indent=2))

    # Return appropriate exit code
    if results["expired"] or results["processed"]:
        # Something happened — agent should review
        sys.exit(0)
    elif pending:
        # Pending items — agent should notify owner
        sys.exit(0)
    else:
        # Nothing to do
        sys.exit(0)

if __name__ == "__main__":
    main()
