#!/usr/bin/env python3
"""
Pipeline Tracker — Budget actuals, outcome measurement, and committee feedback.

Tracks the real cost and impact of improvements so the pipeline can learn
and improve itself over time.

Configuration (environment variables):
  LOOPFORGE_DATA_DIR   — Data directory (default: ~/.loopforge)

Usage:
  pipeline-tracker.py record-cost --id PROP_ID --estimated COST --actual COST
  pipeline-tracker.py record-outcome --id PROP_ID --claimed VALUE --measured VALUE --notes "..."
  pipeline-tracker.py add-feedback --id PROP_ID --member MEMBER --vote VOTE --reason "..."
  pipeline-tracker.py feedback-for-pm                    # Show feedback the PM should read
  pipeline-tracker.py cost-report                        # Show estimate vs actual costs
  pipeline-tracker.py outcome-report                     # Show outcome measurements
  pipeline-tracker.py pm-context                         # Generate PM context for next cycle
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.environ.get("LOOPFORGE_DATA_DIR", os.path.expanduser("~/.loopforge"))) / "data" / "loop-engineer"
COSTS_FILE = DATA_DIR / "cost-actuals.json"
OUTCOMES_FILE = DATA_DIR / "outcomes.json"
FEEDBACK_FILE = DATA_DIR / "committee-feedback.json"
SPRINT_HISTORY_FILE = DATA_DIR / "sprint-history.json"
BUDGET_FILE = DATA_DIR / "sprint-budget.json"


def load_json(path, default=None):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default if default is not None else []


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def record_cost(args):
    """Record actual cost vs estimate for an improvement."""
    costs = load_json(COSTS_FILE, [])
    
    entry = {
        "id": args.id,
        "recorded_at": now_iso(),
        "estimated_cost": args.estimated,
        "actual_cost": args.actual,
        "variance": round(args.actual - args.estimated, 4),
        "variance_pct": round(((args.actual - args.estimated) / args.estimated * 100) if args.estimated > 0 else 0, 1),
    }
    costs.append(entry)
    save_json(COSTS_FILE, costs)

    # Update sprint budget with actual cost
    budget = load_json(BUDGET_FILE, {"budget": 3.00, "spent": 0.00, "remaining": 3.00})
    budget["spent"] = round(budget["spent"] + args.actual, 4)
    budget["remaining"] = round(budget["budget"] - budget["spent"], 4)
    save_json(BUDGET_FILE, budget)

    direction = "over" if args.actual > args.estimated else "under"
    print(f"💰 Cost recorded: {args.id}")
    print(f"   Estimated: ${args.estimated:.2f} | Actual: ${args.actual:.2f}")
    print(f"   Variance: ${abs(entry['variance']):.2f} {direction} estimate")
    print(f"   Sprint budget: ${budget['spent']:.2f} spent / ${budget['remaining']:.2f} remaining")


def record_outcome(args):
    """Record whether an improvement had its claimed impact."""
    outcomes = load_json(OUTCOMES_FILE, [])

    entry = {
        "id": args.id,
        "recorded_at": now_iso(),
        "claimed_value_per_week": args.claimed,
        "measured_value_per_week": args.measured,
        "accuracy": round(args.measured / args.claimed, 2) if args.claimed > 0 else 0,
        "notes": args.notes or "",
        "verified": args.verified,
    }
    outcomes.append(entry)
    save_json(OUTCOMES_FILE, outcomes)

    if entry["accuracy"] >= 0.8:
        verdict = "✅ Accurate (within 20%)"
    elif entry["accuracy"] >= 0.5:
        verdict = "⚠️ Optimistic (claimed 2x+ actual)"
    else:
        verdict = "❌ Inaccurate (claimed 2x+ actual)"

    print(f"📊 Outcome recorded: {args.id}")
    print(f"   Claimed: ${args.claimed:.2f}/week | Measured: ${args.measured:.2f}/week")
    print(f"   Accuracy: {entry['accuracy']:.0%} — {verdict}")
    if args.notes:
        print(f"   Notes: {args.notes}")


def add_feedback(args):
    """Record committee member feedback on a proposal."""
    feedback = load_json(FEEDBACK_FILE, [])

    entry = {
        "id": args.id,
        "recorded_at": now_iso(),
        "member": args.member,
        "vote": args.vote.upper(),
        "reason": args.reason,
    }
    feedback.append(entry)
    save_json(FEEDBACK_FILE, feedback)

    print(f"📝 Feedback recorded: {args.id}")
    print(f"   {args.member}: {args.vote} — {args.reason}")


def feedback_for_pm(args):
    """Show committee feedback the PM should read before generating proposals."""
    feedback = load_json(FEEDBACK_FILE, [])
    if not feedback:
        print("No committee feedback recorded yet.")
        return

    # Group by proposal
    by_proposal = {}
    for f in feedback:
        pid = f["id"]
        if pid not in by_proposal:
            by_proposal[pid] = []
        by_proposal[pid].append(f)

    print("📋 Committee Feedback for PM")
    print("=" * 60)
    print("Read this before generating new proposals. Learn from past decisions.\n")

    for pid, entries in by_proposal.items():
        print(f"--- {pid} ---")
        for e in entries:
            emoji = {"APPROVE": "✅", "ESCALATE": "⚠️", "DEFER": "⏳"}.get(e["vote"], "?")
            print(f"  {emoji} {e['member']}: {e['vote']}")
            print(f"     {e['reason']}")
        print()


def cost_report(args):
    """Show estimate vs actual cost analysis."""
    costs = load_json(COSTS_FILE, [])
    if not costs:
        print("No cost data recorded yet.")
        return

    total_estimated = sum(c["estimated_cost"] for c in costs)
    total_actual = sum(c["actual_cost"] for c in costs)
    total_variance = total_actual - total_estimated

    print("💰 Cost Report")
    print("=" * 60)
    print(f"Total improvements: {len(costs)}")
    print(f"Total estimated: ${total_estimated:.2f}")
    print(f"Total actual: ${total_actual:.2f}")
    print(f"Total variance: ${total_variance:.2f} ({'over' if total_variance > 0 else 'under'} estimate)")
    print(f"Average accuracy: {sum(c['variance_pct'] for c in costs) / len(costs):+.1f}%")
    print()

    print("Per-improvement breakdown:")
    for c in costs:
        direction = "over" if c["variance"] > 0 else "under"
        print(f"  {c['id']}: est ${c['estimated_cost']:.2f} → actual ${c['actual_cost']:.2f} ({abs(c['variance_pct']):.0f}% {direction})")

    # Learn patterns
    if len(costs) >= 3:
        avg_variance = sum(c["variance"] for c in costs) / len(costs)
        print(f"\n📈 Learning:")
        if avg_variance > 0.10:
            print(f"   Estimates are consistently low by ~${avg_variance:.2f}. Adjust estimates up.")
        elif avg_variance < -0.10:
            print(f"   Estimates are consistently high by ~${abs(avg_variance):.2f}. Can be more aggressive.")
        else:
            print(f"   Estimates are reasonably accurate (avg variance: ${avg_variance:+.2f}).")


def outcome_report(args):
    """Show outcome measurement analysis."""
    outcomes = load_json(OUTCOMES_FILE, [])
    if not outcomes:
        print("No outcome data recorded yet.")
        return

    print("📊 Outcome Report")
    print("=" * 60)
    print(f"Total improvements measured: {len(outcomes)}")
    print()

    accurate = sum(1 for o in outcomes if o["accuracy"] >= 0.8)
    optimistic = sum(1 for o in outcomes if 0.5 <= o["accuracy"] < 0.8)
    inaccurate = sum(1 for o in outcomes if o["accuracy"] < 0.5)

    print(f"✅ Accurate (≥80%): {accurate}")
    print(f"⚠️  Optimistic (50-80%): {optimistic}")
    print(f"❌ Inaccurate (<50%): {inaccurate}")
    print()

    print("Per-improvement:")
    for o in outcomes:
        emoji = "✅" if o["accuracy"] >= 0.8 else "⚠️" if o["accuracy"] >= 0.5 else "❌"
        print(f"  {emoji} {o['id']}: claimed ${o['claimed_value_per_week']:.2f}/wk → measured ${o['measured_value_per_week']:.2f}/wk ({o['accuracy']:.0%})")
        if o.get("notes"):
            print(f"     {o['notes']}")

    # Learning for PM
    if outcomes:
        avg_accuracy = sum(o["accuracy"] for o in outcomes) / len(outcomes)
        print(f"\n📈 PM Learning:")
        if avg_accuracy < 0.7:
            print(f"   PM consistently overestimates value (avg accuracy: {avg_accuracy:.0%}).")
            print(f"   Recommend: PM should estimate more conservatively, or validate claims before proposing.")
        elif avg_accuracy > 1.2:
            print(f"   PM consistently underestimates value (avg accuracy: {avg_accuracy:.0%}).")
            print(f"   Recommend: PM can be more ambitious with value estimates.")
        else:
            print(f"   PM estimates are reasonably accurate (avg accuracy: {avg_accuracy:.0%}).")


def pm_context(args):
    """Generate context for the PM's next cycle."""
    feedback = load_json(FEEDBACK_FILE, [])
    costs = load_json(COSTS_FILE, [])
    outcomes = load_json(OUTCOMES_FILE, [])

    context = {
        "generated_at": now_iso(),
        "committee_feedback_summary": "",
        "cost_learning": "",
        "outcome_learning": "",
        "instructions": "",
    }

    # Committee feedback summary
    if feedback:
        deferred = [f for f in feedback if f["vote"] == "DEFER"]
        escalated = [f for f in feedback if f["vote"] == "ESCALATE"]
        approved = [f for f in feedback if f["vote"] == "APPROVE"]

        lines = [f"Past committee decisions ({len(feedback)} total):"]
        lines.append(f"  - {len(approved)} approved, {len(escalated)} escalated, {len(deferred)} deferred")
        if deferred:
            lines.append(f"  - Deferred reasons: {', '.join(set(f['reason'][:60] for f in deferred[:5]))}")
        if escalated:
            lines.append(f"  - Escalated reasons: {', '.join(set(f['reason'][:60] for f in escalated[:5]))}")
        context["committee_feedback_summary"] = "\n".join(lines)

    # Cost learning
    if costs:
        avg_variance = sum(c["variance"] for c in costs) / len(costs)
        if avg_variance > 0.10:
            context["cost_learning"] = f"Historical data shows estimates are low by ~${avg_variance:.2f}. Adjust cost estimates up."
        elif avg_variance < -0.10:
            context["cost_learning"] = f"Historical data shows estimates are high by ~${abs(avg_variance):.2f}. Can be more aggressive."
        else:
            context["cost_learning"] = f"Historical cost estimates are reasonably accurate (avg variance: ${avg_variance:+.2f})."

    # Outcome learning
    if outcomes:
        avg_accuracy = sum(o["accuracy"] for o in outcomes) / len(outcomes)
        if avg_accuracy < 0.7:
            context["outcome_learning"] = f"PM consistently overestimates value (avg accuracy: {avg_accuracy:.0%}). Be more conservative with value_per_week estimates."
        elif avg_accuracy > 1.2:
            context["outcome_learning"] = f"PM underestimates value (avg accuracy: {avg_accuracy:.0%}). Can be more ambitious."
        else:
            context["outcome_learning"] = f"PM value estimates are reasonably accurate (avg accuracy: {avg_accuracy:.0%})."

    # Instructions for PM
    instructions = []
    if context["committee_feedback_summary"]:
        instructions.append("Read committee feedback below and avoid repeating deferred patterns.")
    if context["cost_learning"]:
        instructions.append(context["cost_learning"])
    if context["outcome_learning"]:
        instructions.append(context["outcome_learning"])
    context["instructions"] = " | ".join(instructions) if instructions else "No historical data yet. Generate proposals as normal."

    # Output as PM-readable context
    print("📋 PM Context for Next Cycle")
    print("=" * 60)
    print()
    if context["committee_feedback_summary"]:
        print(context["committee_feedback_summary"])
        print()
    if context["cost_learning"]:
        print(f"💰 {context['cost_learning']}")
        print()
    if context["outcome_learning"]:
        print(f"📊 {context['outcome_learning']}")
        print()
    print(f"📝 Instructions: {context['instructions']}")

    # Also save to file for PM to read
    pm_context_file = DATA_DIR / "pm-context.json"
    save_json(pm_context_file, context)
    print(f"\nSaved to: {pm_context_file}")


def main():
    parser = argparse.ArgumentParser(description="Pipeline Tracker")
    sub = parser.add_subparsers(dest="command")

    p_cost = sub.add_parser("record-cost")
    p_cost.add_argument("--id", required=True)
    p_cost.add_argument("--estimated", type=float, required=True)
    p_cost.add_argument("--actual", type=float, required=True)

    p_outcome = sub.add_parser("record-outcome")
    p_outcome.add_argument("--id", required=True)
    p_outcome.add_argument("--claimed", type=float, required=True)
    p_outcome.add_argument("--measured", type=float, required=True)
    p_outcome.add_argument("--notes", default="")
    p_outcome.add_argument("--verified", default=False, action="store_true")

    p_fb = sub.add_parser("add-feedback")
    p_fb.add_argument("--id", required=True)
    p_fb.add_argument("--member", required=True)
    p_fb.add_argument("--vote", required=True)
    p_fb.add_argument("--reason", required=True)

    sub.add_parser("feedback-for-pm")
    sub.add_parser("cost-report")
    sub.add_parser("outcome-report")
    sub.add_parser("pm-context")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {
        "record-cost": record_cost,
        "record-outcome": record_outcome,
        "add-feedback": add_feedback,
        "feedback-for-pm": feedback_for_pm,
        "cost-report": cost_report,
        "outcome-report": outcome_report,
        "pm-context": pm_context,
    }[args.command](args)


if __name__ == "__main__":
    main()
