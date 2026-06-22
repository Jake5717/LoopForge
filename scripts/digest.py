#!/usr/bin/env python3
"""
LoopForge Digest — plain-English nightly summary, not a diagnostic dump.

Answers three questions in order:
  1. What did the pipeline actually do last night? (from sprint-plan.json)
  2. Is the pipeline itself getting more reliable? (from eval-report.py's history)
  3. What needs me right now? (pending escalations)

This is a thin presentation layer on top of two things that already exist:
  - sprint-plan.json (written by steering-committee.py)
  - eval-history.json (written by eval-report.py)
It does not compute anything new. If eval-report.py hasn't been run for a
given cycle yet, this script runs it first (read-only, same as always).

Configuration (environment variables):
  LOOPFORGE_DATA_DIR   — Data directory (default: ~/.loopforge)

Usage:
  digest.py                  # Today's digest, plain text
  digest.py --date 2026-06-21
  digest.py --format markdown   # for piping into Telegram/Discord/email
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.environ.get("LOOPFORGE_DATA_DIR", os.path.expanduser("~/.loopforge"))) / "data" / "loop-engineer"
SPRINT_PLAN_FILE = DATA_DIR / "sprint-plan.json"
EVAL_HISTORY_FILE = DATA_DIR / "eval-history.json"
SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_SCRIPT = SCRIPT_DIR / "eval-report.py"


def load_json(path, default=None):
    if path.exists():
        with open(path) as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default if default is not None else {}
    return default if default is not None else {}


def today_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def ensure_eval_for_date(cycle_date):
    """Run eval-report.py for this date if it's not already in history."""
    history = load_json(EVAL_HISTORY_FILE, [])
    existing = next((h for h in history if h["cycle_date"] == cycle_date), None)
    if existing:
        return existing
    if not EVAL_SCRIPT.exists():
        return None
    subprocess.run([sys.executable, str(EVAL_SCRIPT), "run", "--date", cycle_date], capture_output=True, timeout=30)
    history = load_json(EVAL_HISTORY_FILE, [])
    return next((h for h in history if h["cycle_date"] == cycle_date), None)


def trend_arrow(history, cycle_date):
    """Compare this cycle's composite to the prior scored cycle."""
    scored = [h for h in history if h.get("composite_score") is not None]
    scored.sort(key=lambda h: h["cycle_date"])
    idx = next((i for i, h in enumerate(scored) if h["cycle_date"] == cycle_date), None)
    if idx is None or idx == 0:
        return None, None
    current = scored[idx]["composite_score"]
    prior = scored[idx - 1]["composite_score"]
    delta = round(current - prior, 2)
    if delta > 0.02:
        arrow = "▲"
    elif delta < -0.02:
        arrow = "▼"
    else:
        arrow = "▬"
    return delta, arrow


def summarize_plan_section(items, decision_label):
    """One line per item: title, cost, ROI if known, why."""
    lines = []
    for item in items:
        title = item.get("title", "untitled")
        cost = item.get("cost_estimate", 0)
        roi = item.get("roi", "N/A")
        reason = item.get("defer_reason") or item.get("note") or ""
        roi_part = f", ROI {roi}" if roi != "N/A" else ""
        reason_part = f" — {reason}" if reason else ""
        lines.append(f"  • {title} (${cost:.2f}{roi_part}){reason_part}")
    return lines


def summarize_escalations(items):
    """Escalations get more detail since they need a human decision."""
    lines = []
    for item in items:
        title = item.get("title", "untitled")
        cost = item.get("cost_estimate", 0)
        risk = item.get("risk", "unknown")
        item_type = item.get("type", "unknown")
        opinions = item.get("opinions", [])
        forced_reason = None
        for o in opinions:
            text = o.get("opinion", "")
            if "[FORCED: security-sensitive type]" in text:
                forced_reason = "security-sensitive"
                break
            if "medium tier" in text:
                forced_reason = "cost over $0.50 threshold"
        why = f" — escalated for {forced_reason}" if forced_reason else ""
        lines.append(f"  • {title} (${cost:.2f}, {item_type}, risk: {risk}){why}")
    return lines


def build_digest(cycle_date, fmt="text"):
    plan = load_json(SPRINT_PLAN_FILE, {})
    eval_record = ensure_eval_for_date(cycle_date)
    history = load_json(EVAL_HISTORY_FILE, [])

    auto_ship = plan.get("auto_ship", [])
    escalate = plan.get("escalate", [])
    defer = plan.get("defer", [])

    composite = eval_record.get("composite_score") if eval_record else None
    delta, arrow = trend_arrow(history, cycle_date) if eval_record else (None, None)

    lines = []
    lines.append(f"LoopForge — {cycle_date}")
    lines.append("=" * 50)
    lines.append("")

    # ── What shipped ──
    if not plan:
        lines.append("No pipeline data found for this cycle yet.")
    elif auto_ship:
        lines.append(f"✅ Shipped tonight ({len(auto_ship)}):")
        lines.extend(summarize_plan_section(auto_ship, "shipped"))
    else:
        lines.append("✅ Shipped tonight: nothing — either an empty cycle or everything needed review.")
    lines.append("")

    # ── What needs you ──
    if escalate:
        lines.append(f"⚠️  Needs your approval ({len(escalate)}):")
        lines.extend(summarize_escalations(escalate))
    else:
        lines.append("⚠️  Needs your approval: nothing pending.")
    lines.append("")

    # ── What got deferred ──
    if defer:
        lines.append(f"⏳ Deferred ({len(defer)}):")
        lines.extend(summarize_plan_section(defer, "deferred"))
        lines.append("")

    # ── Pipeline health ──
    lines.append("📊 Pipeline health:")
    if composite is None:
        lines.append("  No eval data for this cycle (likely an empty/short-circuited night, or eval hasn't run yet).")
    else:
        trend_str = ""
        if arrow:
            sign = "better" if delta > 0 else "worse" if delta < 0 else "same"
            trend_str = f"  {arrow} {sign} than last scored cycle ({delta:+.2f})"
        lines.append(f"  Composite score: {composite:.2f} / 1.00{trend_str}")

        results = eval_record.get("results", {})
        parse = results.get("parse_reliability", {})
        if parse.get("score") is not None and parse["score"] < 0.8:
            fallback_members = [m for m, c in parse.get("per_member", {}).items() if c.get("fallback", 0) > 0]
            if fallback_members:
                lines.append(f"  Watch: {', '.join(fallback_members)} had parsing issues again — known MiMo-style fallback pattern.")
        sentinel = results.get("sentinel_integrity", {})
        if sentinel.get("integrity_issues"):
            lines.append(f"  Watch: sentinel issues on step(s) {sentinel['integrity_issues']} — pipeline may not have run cleanly end-to-end.")
        cascade = results.get("cascade_correctness", {})
        if cascade.get("violations"):
            lines.append(f"  Watch: cascade violation at step(s) {cascade['violations']} — a step ran when it should have short-circuited.")

    lines.append("")
    return "\n".join(lines) if fmt == "text" else to_markdown(lines)


def to_markdown(lines):
    # Minimal conversion: title becomes a header, section labels become bold.
    out = []
    for i, line in enumerate(lines):
        if i == 0:
            out.append(f"### {line}")
        elif line.startswith("="):
            continue
        else:
            out.append(line)
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="LoopForge nightly digest")
    parser.add_argument("--date", help="Cycle date YYYY-MM-DD (default: today, UTC)")
    parser.add_argument("--format", choices=["text", "markdown"], default="text")
    args = parser.parse_args()

    cycle_date = args.date or today_str()
    print(build_digest(cycle_date, fmt=args.format))


if __name__ == "__main__":
    main()
