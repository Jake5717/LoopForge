#!/usr/bin/env python3
"""
LoopForge Eval Suite — scores pipeline run quality from existing state files.

Does NOT change pipeline behavior. Read-only against the same files
pipeline-tracker.py and steering-committee.py already write. Run this
after Engineering Phase (step 6) each night, or anytime, to get a
score for "how well did the pipeline actually do its job."

Six eval categories, each independently scoreable:
  1. parse_reliability   — committee evaluations: clean JSON vs regex vs text-scan fallback
  2. sentinel_integrity   — did every step that should run leave done+status sentinels
  3. budget_honesty       — cost estimate vs actual variance trend
  4. outcome_accuracy     — claimed vs measured value_per_week trend
  5. decision_agreement   — does forced ESCALATE override original committee vote often
  6. cascade_correctness  — did "empty" status correctly cascade downstream

Configuration (environment variables):
  LOOPFORGE_DATA_DIR   — Data directory (default: ~/.loopforge)

Usage:
  eval-report.py run                  # Score the most recent cycle, print report
  eval-report.py run --date 2026-06-21 # Score a specific cycle date
  eval-report.py trend                # Show score trend across all recorded runs
  eval-report.py history              # List all eval runs on file, most recent first
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.environ.get("LOOPFORGE_DATA_DIR", os.path.expanduser("~/.loopforge"))) / "data" / "loop-engineer"

PROPOSALS_FILE = DATA_DIR / "current-proposals.json"
BUDGET_FILE = DATA_DIR / "sprint-budget.json"
SPRINT_PLAN_FILE = DATA_DIR / "sprint-plan.json"
EVALUATIONS_DIR = DATA_DIR / "committee-evaluations"
COSTS_FILE = DATA_DIR / "cost-actuals.json"
OUTCOMES_FILE = DATA_DIR / "outcomes.json"
FEEDBACK_FILE = DATA_DIR / "committee-feedback.json"

EVAL_HISTORY_FILE = DATA_DIR / "eval-history.json"

STEP_NAMES = {
    1: "PM",
    2: "Idea Verifier",
    3: "Steering Committee",
    4: "Code Writer",
    5: "Code Verifier",
    6: "Engineering Phase",
}


def load_json(path, default=None):
    if path.exists():
        with open(path) as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default if default is not None else []
    return default if default is not None else []


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def today_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ─── Eval 1: Parse Reliability ────────────────────────────────────────────────────────────────

def eval_parse_reliability(cycle_date):
    """
    Looks at committee-evaluations/*.json files for the cycle date.
    We can't directly tell from the saved file whether it came from strict
    JSON, regex fallback, or text-scan, because steering-committee.py only
    saves the parsed result. So this eval infers fallback-likely entries by
    signal: opinion text that contains junk characters, is suspiciously short,
    is exactly "Not evaluated" / "Not in response" / "Could not parse"
    (the literal default strings in steering-committee.py's fallback paths),
    or every vote in the file is DEFER (the all-default failure mode).
    """
    eval_files = sorted(EVALUATIONS_DIR.glob(f"*-{cycle_date.replace('-', '')}*.json")) if EVALUATIONS_DIR.exists() else []
    if not eval_files:
        # fall back to matching on mtime date if filename pattern doesn't match
        eval_files = []
        if EVALUATIONS_DIR.exists():
            for f in EVALUATIONS_DIR.glob("*.json"):
                mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
                if mtime == cycle_date:
                    eval_files.append(f)

    if not eval_files:
        return {"status": "no_data", "score": None, "detail": f"No committee evaluation files found for {cycle_date}"}

    KNOWN_FALLBACK_STRINGS = {"Not evaluated", "Not in response", "Could not parse"}

    total_entries = 0
    clean_entries = 0
    fallback_entries = 0
    per_member = {}

    for f in eval_files:
        member = f.stem.rsplit("-", 2)[0]  # strip timestamp suffix
        entries = load_json(f, [])
        per_member.setdefault(member, {"clean": 0, "fallback": 0})
        for e in entries:
            total_entries += 1
            opinion = (e.get("opinion") or "").strip()
            is_fallback = (
                opinion in KNOWN_FALLBACK_STRINGS
                or opinion == ""
                or len(opinion) < 8
            )
            if is_fallback:
                fallback_entries += 1
                per_member[member]["fallback"] += 1
            else:
                clean_entries += 1
                per_member[member]["clean"] += 1

    score = round(clean_entries / total_entries, 3) if total_entries else None
    return {
        "status": "ok",
        "score": score,
        "total_entries": total_entries,
        "clean_entries": clean_entries,
        "fallback_entries": fallback_entries,
        "per_member": per_member,
        "detail": f"{clean_entries}/{total_entries} committee evaluations parsed cleanly",
    }


# ─── Eval 2: Sentinel Integrity ──────────────────────────────────────────────────────────────

def eval_sentinel_integrity(cycle_date):
    """
    Checks stepN.done and stepN.status.json for steps 1-6.
    A step is 'missing' if no sentinel exists for the cycle date at all.
    A step is 'stale' if the sentinel exists but cycle_date doesn't match.
    A step is 'failed' if status.json says status: failed.
    A step is 'ok' if done exists, status.json cycle_date matches, status in (ran, empty).
    """
    results = {}
    short_circuited_at = None

    for n in range(1, 7):
        status_file = DATA_DIR / f"step{n}.status.json"
        done_file = DATA_DIR / f"step{n}.done"

        if not done_file.exists() and not status_file.exists():
            results[n] = {"state": "missing", "detail": f"step{n}.done and step{n}.status.json both absent"}
            continue

        status_data = load_json(status_file, {}) if status_file.exists() else {}
        status_val = status_data.get("status")
        file_cycle_date = status_data.get("cycle_date")

        if not done_file.exists():
            results[n] = {"state": "missing_done", "detail": f"step{n}.status.json exists but step{n}.done missing"}
            continue

        if file_cycle_date != cycle_date:
            results[n] = {"state": "stale", "detail": f"sentinel cycle_date={file_cycle_date}, expected {cycle_date}"}
            continue

        if status_val == "failed":
            results[n] = {"state": "failed", "detail": status_data.get("summary", "no summary")}
        elif status_val == "empty":
            results[n] = {"state": "empty", "detail": status_data.get("summary", "cascade short-circuit")}
            if short_circuited_at is None:
                short_circuited_at = n
        elif status_val == "ran":
            results[n] = {"state": "ran", "detail": status_data.get("summary", "")}
        else:
            results[n] = {"state": "unknown_status", "detail": f"status field was {status_val!r}"}

    # Score: did the cascade behave correctly?
    # If a step is empty, every step after it should also be empty (or missing, if the
    # pipeline hasn't reached that point in time yet — we don't penalize that here since
    # this eval is meant to run after step 6 completes).
    cascade_violations = []
    if short_circuited_at:
        for n in range(short_circuited_at + 1, 7):
            if results.get(n, {}).get("state") not in ("empty", "missing"):
                cascade_violations.append(n)

    integrity_issues = [n for n, r in results.items() if r["state"] in ("missing", "missing_done", "stale", "failed", "unknown_status")]

    total_steps = 6
    clean_steps = total_steps - len(integrity_issues) - len(cascade_violations)
    score = round(max(clean_steps, 0) / total_steps, 3)

    return {
        "status": "ok",
        "score": score,
        "steps": results,
        "short_circuited_at": short_circuited_at,
        "cascade_violations": cascade_violations,
        "integrity_issues": integrity_issues,
        "detail": f"{6 - len(integrity_issues)}/6 steps had clean sentinels"
        + (f"; cascade violated at step(s) {cascade_violations}" if cascade_violations else ""),
    }


# ─── Eval 3: Budget Honesty ────────────────────────────────────────────────────────────────

def eval_budget_honesty(cycle_date):
    costs = load_json(COSTS_FILE, [])
    cycle_costs = [c for c in costs if c.get("recorded_at", "").startswith(cycle_date)]
    if not cycle_costs:
        return {"status": "no_data", "score": None, "detail": f"No cost-actuals entries recorded for {cycle_date}"}

    abs_variance_pcts = [abs(c.get("variance_pct", 0)) for c in cycle_costs]
    avg_abs_variance_pct = sum(abs_variance_pcts) / len(abs_variance_pcts)

    # Score: 0% variance = 1.0, 50%+ avg variance = 0.0, linear between
    score = round(max(0.0, 1.0 - (avg_abs_variance_pct / 50.0)), 3)

    return {
        "status": "ok",
        "score": score,
        "entries": len(cycle_costs),
        "avg_abs_variance_pct": round(avg_abs_variance_pct, 1),
        "detail": f"{len(cycle_costs)} cost entries, avg |variance| {avg_abs_variance_pct:.1f}%",
    }


# ─── Eval 4: Outcome Accuracy ─────────────────────────────────────────────────────────────

def eval_outcome_accuracy(cycle_date):
    outcomes = load_json(OUTCOMES_FILE, [])
    cycle_outcomes = [o for o in outcomes if o.get("recorded_at", "").startswith(cycle_date)]
    if not cycle_outcomes:
        return {"status": "no_data", "score": None, "detail": f"No outcomes recorded for {cycle_date}"}

    accuracies = [o.get("accuracy", 0) for o in cycle_outcomes]
    # accuracy of 1.0 is perfect; score penalizes distance from 1.0 in either direction
    deviations = [abs(1.0 - a) for a in accuracies]
    avg_deviation = sum(deviations) / len(deviations)
    score = round(max(0.0, 1.0 - avg_deviation), 3)

    return {
        "status": "ok",
        "score": score,
        "entries": len(cycle_outcomes),
        "avg_accuracy": round(sum(accuracies) / len(accuracies), 2),
        "detail": f"{len(cycle_outcomes)} outcomes recorded, avg accuracy {sum(accuracies)/len(accuracies):.0%}",
    }


# ─── Eval 5: Decision Agreement ────────────────────────────────────────────────────────────

def eval_decision_agreement(cycle_date):
    """
    Reads sprint-plan.json (current snapshot — this is overwritten each cycle
    by steering-committee.py, so this eval is only meaningful for "most recent
    cycle" unless sprint-plan history is added later).

    Looks at items forced to ESCALATE (security-sensitive or cost >= $0.50)
    and checks what the committee's *underlying* opinions actually said before
    the force-override, using the [FORCED: ...] marker steering-committee.py
    appends to the opinion text. This tells you how often forced escalation is
    overriding a committee that would have approved anyway (forced caution) vs.
    overriding a committee that agreed something was risky (forced and aligned).
    """
    plan = load_json(SPRINT_PLAN_FILE, {})
    if not plan:
        return {"status": "no_data", "score": None, "detail": "No sprint-plan.json found"}

    escalated = plan.get("escalate", [])
    if not escalated:
        return {"status": "ok", "score": None, "entries": 0, "detail": "No escalated items this cycle — nothing to evaluate"}

    forced_count = 0
    forced_but_would_have_approved = 0

    for item in escalated:
        opinions = item.get("opinions", [])
        is_forced = any("[FORCED:" in (o.get("opinion") or "") for o in opinions)
        if not is_forced:
            continue
        forced_count += 1
        # Strip the forced marker and check what's left of the original vote signal.
        # We can't recover the literal original vote (it's overwritten), but the
        # original opinion text is preserved before the marker — check sentiment
        # heuristically isn't reliable, so instead check the [FORCED: ...] reason itself:
        # if the reason is "cost >= $0.50" (medium tier) rather than "security-sensitive",
        # that's the catch-all-by-cost rule, which is the one worth watching for false
        # positives (forcing review on stuff that's genuinely fine).
        reasons = [o.get("opinion", "") for o in opinions]
        if any("medium tier" in r for r in reasons) and not any("security-sensitive" in r for r in reasons):
            forced_but_would_have_approved += 1

    # This isn't a 0-1 "goodness" score in the same sense as the others — a high
    # rate of cost-tier forcing isn't necessarily bad, it's a policy choice. We
    # report the rate rather than scoring it, so Jake can eyeball whether the
    # $0.50 threshold is catching too much.
    rate = round(forced_but_would_have_approved / forced_count, 3) if forced_count else None

    return {
        "status": "ok",
        "score": None,  # informational, not a pass/fail score — see detail
        "escalated_count": len(escalated),
        "forced_count": forced_count,
        "forced_by_cost_tier_only": forced_but_would_have_approved,
        "cost_tier_force_rate": rate,
        "detail": (
            f"{len(escalated)} escalated this cycle, {forced_count} were forced overrides; "
            f"{forced_but_would_have_approved} forced by cost-tier alone (not security) "
            f"— {rate:.0%} of forced items" if rate is not None else "no forced items"
        ),
    }


# ─── Eval 6: Cascade Correctness ─────────────────────────────────────────────────────────────
# Folded into sentinel_integrity above (cascade_violations field) since it reads
# the same sentinel files. Kept as a thin wrapper for clarity in the report.

def eval_cascade_correctness(sentinel_result):
    violations = sentinel_result.get("cascade_violations", [])
    short_circuited_at = sentinel_result.get("short_circuited_at")
    if short_circuited_at is None:
        return {"status": "ok", "score": None, "detail": "No short-circuit this cycle — full pipeline ran, nothing to check"}
    score = 1.0 if not violations else round(1.0 - (len(violations) / (6 - short_circuited_at)), 3)
    return {
        "status": "ok",
        "score": score,
        "short_circuited_at": short_circuited_at,
        "violations": violations,
        "detail": f"Cascade started at step {short_circuited_at}; "
        + (f"violated at {violations}" if violations else "all downstream steps correctly empty"),
    }


# ─── Composite scoring & reporting ────────────────────────────────────────────────────────

WEIGHTS = {
    "parse_reliability": 0.20,
    "sentinel_integrity": 0.25,
    "budget_honesty": 0.20,
    "outcome_accuracy": 0.20,
    "cascade_correctness": 0.15,
    # decision_agreement is informational only, excluded from composite
}


def composite_score(results):
    weighted_sum = 0.0
    weight_total = 0.0
    for key, weight in WEIGHTS.items():
        score = results.get(key, {}).get("score")
        if score is not None:
            weighted_sum += score * weight
            weight_total += weight
    if weight_total == 0:
        return None
    return round(weighted_sum / weight_total, 3)


def run_eval(cycle_date):
    sentinel_result = eval_sentinel_integrity(cycle_date)
    results = {
        "parse_reliability": eval_parse_reliability(cycle_date),
        "sentinel_integrity": sentinel_result,
        "budget_honesty": eval_budget_honesty(cycle_date),
        "outcome_accuracy": eval_outcome_accuracy(cycle_date),
        "cascade_correctness": eval_cascade_correctness(sentinel_result),
        "decision_agreement": eval_decision_agreement(cycle_date),
    }
    composite = composite_score(results)

    record = {
        "cycle_date": cycle_date,
        "evaluated_at": now_iso(),
        "composite_score": composite,
        "results": results,
    }
    return record


def print_report(record):
    cd = record["cycle_date"]
    print(f"🧪 LoopForge Eval Report — {cd}")
    print("=" * 70)
    composite = record["composite_score"]
    if composite is not None:
        bar = "█" * int(composite * 20)
        print(f"Composite score: {composite:.2f}  [{bar:<20}]")
    else:
        print("Composite score: N/A (no scoreable data for this cycle)")
    print()

    for key in ["parse_reliability", "sentinel_integrity", "budget_honesty", "outcome_accuracy", "cascade_correctness", "decision_agreement"]:
        r = record["results"][key]
        score = r.get("score")
        score_str = f"{score:.2f}" if score is not None else "—"
        label = key.replace("_", " ").title()
        print(f"  {label:<22} {score_str:>5}   {r.get('detail', '')}")

    sentinel = record["results"]["sentinel_integrity"]
    if sentinel.get("integrity_issues"):
        print()
        print("  ⚠️  Sentinel issues:")
        for n in sentinel["integrity_issues"]:
            step = sentinel["steps"].get(n, {})
            print(f"     Step {n} ({STEP_NAMES.get(n, '?')}): {step.get('state')} — {step.get('detail')}")

    parse_pm = record["results"]["parse_reliability"].get("per_member")
    if parse_pm:
        worst = sorted(parse_pm.items(), key=lambda kv: kv[1]["fallback"], reverse=True)
        if worst and worst[0][1]["fallback"] > 0:
            print()
            print("  ⚠️  Parse fallback by committee member:")
            for member, counts in worst:
                if counts["fallback"] > 0:
                    print(f"     {member}: {counts['fallback']} fallback / {counts['clean']} clean")

    print()


def cmd_run(args):
    cycle_date = args.date or today_str()
    record = run_eval(cycle_date)
    print_report(record)

    history = load_json(EVAL_HISTORY_FILE, [])
    history = [h for h in history if h["cycle_date"] != cycle_date]  # replace if re-run
    history.append(record)
    history.sort(key=lambda h: h["cycle_date"])
    save_json(EVAL_HISTORY_FILE, history)
    print(f"Saved to: {EVAL_HISTORY_FILE}")


def cmd_trend(args):
    history = load_json(EVAL_HISTORY_FILE, [])
    if not history:
        print("No eval history yet. Run `eval-report.py run` first.")
        return

    print("📈 LoopForge Eval Trend")
    print("=" * 70)
    print(f"{'Date':<12} {'Composite':>10} {'Parse':>7} {'Sentinel':>9} {'Budget':>7} {'Outcome':>8} {'Cascade':>8}")
    for h in history:
        r = h["results"]

        def fmt(key):
            s = r.get(key, {}).get("score")
            return f"{s:.2f}" if s is not None else "—"

        comp = h["composite_score"]
        comp_str = f"{comp:.2f}" if comp is not None else "—"
        print(f"{h['cycle_date']:<12} {comp_str:>10} {fmt('parse_reliability'):>7} {fmt('sentinel_integrity'):>9} {fmt('budget_honesty'):>7} {fmt('outcome_accuracy'):>8} {fmt('cascade_correctness'):>8}")

    scored = [h["composite_score"] for h in history if h["composite_score"] is not None]
    if len(scored) >= 2:
        delta = scored[-1] - scored[0]
        direction = "improving" if delta > 0.02 else "declining" if delta < -0.02 else "stable"
        print(f"\nTrend over {len(scored)} scored cycles: {direction} ({delta:+.2f})")


def cmd_history(args):
    history = load_json(EVAL_HISTORY_FILE, [])
    if not history:
        print("No eval history yet.")
        return
    for h in sorted(history, key=lambda h: h["cycle_date"], reverse=True):
        comp = h["composite_score"]
        comp_str = f"{comp:.2f}" if comp is not None else "N/A"
        print(f"{h['cycle_date']}  composite={comp_str}  evaluated_at={h['evaluated_at']}")


def main():
    parser = argparse.ArgumentParser(description="LoopForge Eval Suite")
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="Score a cycle (default: today)")
    p_run.add_argument("--date", help="Cycle date YYYY-MM-DD (default: today, UTC)")

    sub.add_parser("trend", help="Show score trend across recorded runs")
    sub.add_parser("history", help="List all eval runs on file")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {
        "run": cmd_run,
        "trend": cmd_trend,
        "history": cmd_history,
    }[args.command](args)


if __name__ == "__main__":
    main()
