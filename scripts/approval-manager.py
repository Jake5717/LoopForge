#!/usr/bin/env python3
"""
Approval Manager — Asynchronous human-in-the-loop approval mechanism.

Manages security-sensitive and governance-tiered changes through a
propose → approve/deny → process lifecycle.

Configuration (environment variables):
  LOOPFORGE_DATA_DIR   — Data directory (default: ~/.loopforge)
  LOOPFORGE_OWNER      — Owner name for approvals (default: "owner")

Usage:
  approval-manager.py propose --title "..." --description "..." --risk low|medium|high|critical --type security|improvement|config [--expires-hours N] [--context-file PATH]
  approval-manager.py approve --id ID [--note "..."]
  approval-manager.py deny --id ID --reason "..."
  approval-manager.py process [--dry-run]
  approval-manager.py check-expired
  approval-manager.py status [--id ID]
  approval-manager.py digest
  approval-manager.py rollback-info --id ID
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(os.environ.get("LOOPFORGE_DATA_DIR", os.path.expanduser("~/.loopforge")))
APPROVALS_DIR = BASE_DIR / "approvals"
PENDING_DIR = APPROVALS_DIR / "pending"
APPROVED_DIR = APPROVALS_DIR / "approved"
DENIED_DIR = APPROVALS_DIR / "denied"
EXPIRED_DIR = APPROVALS_DIR / "expired"
APPLIED_DIR = APPROVALS_DIR / "applied"
ROLLBACK_DIR = APPROVALS_DIR / "rollbacks"

OWNER = os.environ.get("LOOPFORGE_OWNER", "owner")

# Default expiration: 72 hours
DEFAULT_EXPIRE_HOURS = 72

# Security-sensitive change types that ALWAYS require approval
SECURITY_TYPES = {"firewall_rule", "dns_config", "ssh_key", "certificate", "vlan_change", "permission_change", "credential_update"}

# Risk-based expiration overrides (hours)
RISK_EXPIRY = {
    "critical": 24,
    "high": 48,
    "medium": 72,
    "low": 168,  # 7 days
}


def ensure_dirs():
    """Create all approval directories if they don't exist."""
    for d in [APPROVALS_DIR, PENDING_DIR, APPROVED_DIR, DENIED_DIR, EXPIRED_DIR, APPLIED_DIR, ROLLBACK_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def gen_id():
    """Generate a unique approval ID."""
    now = datetime.now(timezone.utc)
    return f"apr-{now.strftime('%Y%m%d-%H%M')}-{uuid.uuid4().hex[:6]}"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def propose(args):
    """Create a new approval proposal."""
    ensure_dirs()

    approval_id = gen_id()
    created = datetime.now(timezone.utc)

    # Determine expiration based on risk level
    if args.expires_hours:
        expires = created + timedelta(hours=args.expires_hours)
    else:
        hours = RISK_EXPIRY.get(args.risk, DEFAULT_EXPIRE_HOURS)
        expires = created + timedelta(hours=hours)

    # Load context if provided
    context = {}
    if args.context_file:
        try:
            with open(args.context_file) as f:
                context = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load context file: {e}", file=sys.stderr)

    proposal = {
        "id": approval_id,
        "created": created.isoformat(),
        "expires": expires.isoformat(),
        "type": args.type,
        "risk": args.risk,
        "title": args.title,
        "description": args.description,
        "status": "pending",
        "proposed_by": args.proposed_by or "unknown",
        "context": context,
        "rollback_window_runs": args.rollback_runs or 3,
        "notes": [],
    }

    # Security-sensitive changes are always flagged
    if args.type in SECURITY_TYPES:
        proposal["security_sensitive"] = True
        proposal["requires_owner_approval"] = True

    # Write to pending directory
    filepath = PENDING_DIR / f"{approval_id}.json"
    with open(filepath, "w") as f:
        json.dump(proposal, f, indent=2)

    print(f"✅ Proposal created: {approval_id}")
    print(f"   Title: {args.title}")
    print(f"   Risk: {args.risk}")
    print(f"   Expires: {expires.isoformat()}")
    if proposal.get("security_sensitive"):
        print(f"   ⚠️  SECURITY-SENSITIVE — requires explicit approval")
    print(f"   File: {filepath}")

    return proposal


def approve(args):
    """Approve a pending proposal."""
    ensure_dirs()

    src = PENDING_DIR / f"{args.id}.json"
    if not src.exists():
        print(f"❌ Not found: {args.id}", file=sys.stderr)
        sys.exit(1)

    with open(src) as f:
        proposal = json.load(f)

    proposal["status"] = "approved"
    proposal["approved_at"] = now_iso()
    proposal["approved_by"] = args.approved_by or OWNER
    if args.note:
        proposal["notes"].append({"by": args.approved_by or OWNER, "text": args.note, "at": now_iso()})

    # Move to approved directory
    dst = APPROVED_DIR / f"{args.id}.json"
    src.rename(dst)

    print(f"✅ Approved: {args.id}")
    print(f"   Title: {proposal['title']}")
    return proposal


def deny(args):
    """Deny a pending proposal."""
    ensure_dirs()

    src = PENDING_DIR / f"{args.id}.json"
    if not src.exists():
        print(f"❌ Not found: {args.id}", file=sys.stderr)
        sys.exit(1)

    with open(src) as f:
        proposal = json.load(f)

    proposal["status"] = "denied"
    proposal["denied_at"] = now_iso()
    proposal["denied_by"] = args.denied_by or OWNER
    proposal["deny_reason"] = args.reason

    dst = DENIED_DIR / f"{args.id}.json"
    src.rename(dst)

    print(f"❌ Denied: {args.id}")
    print(f"   Title: {proposal['title']}")
    print(f"   Reason: {args.reason}")
    return proposal


def check_expired(args):
    """Move expired proposals from pending to expired directory."""
    ensure_dirs()
    now = datetime.now(timezone.utc)
    expired_count = 0

    for f in PENDING_DIR.glob("apr-*.json"):
        with open(f) as fh:
            proposal = json.load(fh)

        expires = datetime.fromisoformat(proposal["expires"])
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        if now > expires:
            proposal["status"] = "expired"
            proposal["expired_at"] = now_iso()
            dst = EXPIRED_DIR / f.name
            f.rename(dst)
            expired_count += 1
            print(f"⏰ Expired: {proposal['id']} — {proposal['title']}")

    if expired_count == 0:
        print("No expired proposals.")
    else:
        print(f"\n{expired_count} proposal(s) expired.")
    return expired_count


def process(args):
    """Apply all approved proposals. Dry-run mode available."""
    ensure_dirs()
    processed = 0

    for f in sorted(APPROVED_DIR.glob("apr-*.json")):
        with open(f) as fh:
            proposal = json.load(fh)

        print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Processing: {proposal['id']}")
        print(f"  Title: {proposal['title']}")
        print(f"  Type: {proposal['type']}")
        print(f"  Risk: {proposal['risk']}")

        if not args.dry_run:
            proposal["status"] = "applied"
            proposal["applied_at"] = now_iso()
            dst = APPLIED_DIR / f.name
            f.rename(dst)
            print(f"  ✅ Applied and moved to applied/")
        else:
            print(f"  📋 Would apply (dry run)")

        processed += 1

    if processed == 0:
        print("No approved proposals to process.")
    else:
        print(f"\n{processed} proposal(s) {'would be ' if args.dry_run else ''}processed.")
    return processed


def status(args):
    """Show current approval status."""
    ensure_dirs()

    if args.id:
        # Show specific proposal
        for directory in [PENDING_DIR, APPROVED_DIR, DENIED_DIR, EXPIRED_DIR, APPLIED_DIR]:
            filepath = directory / f"{args.id}.json"
            if filepath.exists():
                with open(filepath) as f:
                    proposal = json.load(f)
                print(json.dumps(proposal, indent=2))
                return proposal
        print(f"❌ Not found: {args.id}", file=sys.stderr)
        sys.exit(1)

    # Show summary
    counts = {}
    items = {}
    for status_name, directory in [("pending", PENDING_DIR), ("approved", APPROVED_DIR),
                                     ("denied", DENIED_DIR), ("expired", EXPIRED_DIR),
                                     ("applied", APPLIED_DIR)]:
        files = list(directory.glob("apr-*.json"))
        counts[status_name] = len(files)
        items[status_name] = []
        for f in sorted(files):
            with open(f) as fh:
                p = json.load(fh)
            items[status_name].append({
                "id": p["id"],
                "title": p["title"],
                "risk": p["risk"],
                "type": p["type"],
                "created": p["created"],
                "expires": p.get("expires"),
            })

    print("📊 Approval Status")
    print("=" * 50)
    for status_name in ["pending", "approved", "denied", "expired", "applied"]:
        count = counts[status_name]
        emoji = {"pending": "⏳", "approved": "✅", "denied": "❌", "expired": "⏰", "applied": "🚀"}[status_name]
        print(f"\n{emoji} {status_name.upper()} ({count})")
        for item in items[status_name]:
            print(f"  • [{item['risk']}] {item['id']}: {item['title']}")
            if item.get("expires") and status_name == "pending":
                print(f"    Expires: {item['expires']}")

    return counts


def digest(args):
    """Generate a weekly digest for the owner."""
    ensure_dirs()

    # Count items in each directory
    pending = list(PENDING_DIR.glob("apr-*.json"))
    approved = list(APPROVED_DIR.glob("apr-*.json"))
    applied = list(APPLIED_DIR.glob("apr-*.json"))
    denied = list(DENIED_DIR.glob("apr-*.json"))
    expired = list(EXPIRED_DIR.glob("apr-*.json"))

    lines = ["## 📋 Approval Digest", ""]

    if pending:
        lines.append(f"### ⏳ Pending Your Approval ({len(pending)})")
        for f in sorted(pending):
            with open(f) as fh:
                p = json.load(fh)
            sec = " 🔒 SECURITY" if p.get("security_sensitive") else ""
            lines.append(f"- **{p['id']}**: {p['title']} [{p['risk']}]{sec}")
            lines.append(f"  {p['description'][:200]}")
            lines.append(f"  Expires: {p['expires']}")
            lines.append("")
    else:
        lines.append("### ⏳ Pending Your Approval (0)")
        lines.append("None! 🎉")
        lines.append("")

    if applied:
        lines.append(f"### 🚀 Applied This Period ({len(applied)})")
        for f in sorted(applied):
            with open(f) as fh:
                p = json.load(fh)
            lines.append(f"- **{p['id']}**: {p['title']} [{p['risk']}]")
        lines.append("")

    if denied:
        lines.append(f"### ❌ Denied ({len(denied)})")
        for f in sorted(denied):
            with open(f) as fh:
                p = json.load(fh)
            reason = p.get("deny_reason", "no reason")
            lines.append(f"- **{p['id']}**: {p['title']} — {reason}")
        lines.append("")

    if expired:
        lines.append(f"### ⏰ Expired ({len(expired)})")
        for f in sorted(expired):
            with open(f) as fh:
                p = json.load(fh)
            lines.append(f"- **{p['id']}**: {p['title']}")
        lines.append("")

    digest_text = "\n".join(lines)
    print(digest_text)
    return digest_text


def rollback_info(args):
    """Show rollback information for a specific approval."""
    ensure_dirs()

    # Search all directories
    for directory in [PENDING_DIR, APPROVED_DIR, APPLIED_DIR, DENIED_DIR, EXPIRED_DIR]:
        filepath = directory / f"{args.id}.json"
        if filepath.exists():
            with open(filepath) as f:
                proposal = json.load(f)

            runs = proposal.get("rollback_window_runs", 3)
            print(f"🔄 Rollback Info: {proposal['id']}")
            print(f"   Title: {proposal['title']}")
            print(f"   Rollback window: {runs} runs")
            if proposal.get("context", {}).get("baseline_file"):
                print(f"   Baseline: {proposal['context']['baseline_file']}")
            if proposal.get("context", {}).get("original_hash"):
                print(f"   Original hash: {proposal['context']['original_hash']}")
            return proposal

    print(f"❌ Not found: {args.id}", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Approval Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # propose
    p_propose = subparsers.add_parser("propose", help="Create a new approval proposal")
    p_propose.add_argument("--title", required=True, help="Proposal title")
    p_propose.add_argument("--description", required=True, help="Detailed description")
    p_propose.add_argument("--risk", required=True, choices=["low", "medium", "high", "critical"], help="Risk level")
    p_propose.add_argument("--type", required=True, help="Change type (security, improvement, config, firewall_rule, dns_config, etc.)")
    p_propose.add_argument("--expires-hours", type=int, help="Custom expiration in hours (default: risk-based)")
    p_propose.add_argument("--context-file", help="Path to JSON context file")
    p_propose.add_argument("--proposed-by", help="Who proposed this (default: unknown)")
    p_propose.add_argument("--rollback-runs", type=int, default=3, help="Rollback window in runs (default: 3)")

    # approve
    p_approve = subparsers.add_parser("approve", help="Approve a pending proposal")
    p_approve.add_argument("--id", required=True, help="Approval ID")
    p_approve.add_argument("--note", help="Optional note")
    p_approve.add_argument("--approved-by", help="Who approved (default: owner)")

    # deny
    p_deny = subparsers.add_parser("deny", help="Deny a pending proposal")
    p_deny.add_argument("--id", required=True, help="Approval ID")
    p_deny.add_argument("--reason", required=True, help="Reason for denial")
    p_deny.add_argument("--denied-by", help="Who denied (default: owner)")

    # process
    p_process = subparsers.add_parser("process", help="Apply approved proposals")
    p_process.add_argument("--dry-run", action="store_true", help="Preview without applying")

    # check-expired
    subparsers.add_parser("check-expired", help="Move expired proposals to expired directory")

    # status
    p_status = subparsers.add_parser("status", help="Show approval status")
    p_status.add_argument("--id", help="Show specific proposal details")

    # digest
    subparsers.add_parser("digest", help="Generate weekly digest for owner")

    # rollback-info
    p_rollback = subparsers.add_parser("rollback-info", help="Show rollback info for a proposal")
    p_rollback.add_argument("--id", required=True, help="Approval ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "propose": propose,
        "approve": approve,
        "deny": deny,
        "process": process,
        "check-expired": check_expired,
        "status": status,
        "digest": digest,
        "rollback-info": rollback_info,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
