#!/usr/bin/env python3
"""
Steering Committee — 3-member evaluation with genuine analysis.

Members (all content-agnostic, evaluate any proposal type):
  1. Budget Analyst (MiMo 2.5) — cost, value, ROI, budget fit
  2. Risk Assessor (Gemini 2.5 Flash) — blast radius, security, failure modes
  3. Priority Arbitrator (GPT-4o Mini) — impact, timing, opportunity cost

Each member provides genuine analysis and opinion, not rule-checking.
ROI is calculated from the PM's value_estimate / cost_estimate.

Configuration (environment variables):
  LOOPFORGE_DATA_DIR   — Data directory (default: ~/.loopforge)
  LOOPFORGE_OWNER      — Owner name for approvals (default: "owner")

Usage:
  steering-committee.py evaluate   # Run full 3-member evaluation + vote
  steering-committee.py status     # Show current sprint status
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

DATA_DIR = Path(os.environ.get("LOOPFORGE_DATA_DIR", os.path.expanduser("~/.loopforge"))) / "data" / "loop-engineer"
PROPOSALS_FILE = DATA_DIR / "current-proposals.json"
BUDGET_FILE = DATA_DIR / "sprint-budget.json"
SPRINT_PLAN_FILE = DATA_DIR / "sprint-plan.json"
EVALUATIONS_DIR = DATA_DIR / "committee-evaluations"

OWNER = os.environ.get("LOOPFORGE_OWNER", "owner")

SECURITY_TYPES = {"firewall_rule", "dns_config", "ssh_key", "certificate", "vlan_change", "permission_change", "credential_update"}


def load_env():
    env_path = os.path.join(str(DATA_DIR.parent.parent), ".env")
    env = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env[key.strip()] = value.strip().strip("'\"")
    return env

ENV = load_env()

MEMBERS = {
    "budget_analyst": {
        "name": "Budget Analyst",
        "model": "mimo-v2.5",
        "base_url": "https://api.xiaomimimo.com/v1",
        "api_key_env": "XIAOMI_API_KEY",
    },
    "risk_assessor": {
        "name": "Risk Assessor",
        "model": "google/gemini-2.5-flash",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "priority_arbitrator": {
        "name": "Priority Arbitrator",
        "model": "openai/gpt-4o-mini",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
    },
}


def call_model(member_config, system_prompt, user_prompt):
    api_key = ENV.get(member_config["api_key_env"], "")
    if not api_key:
        return f"ERROR: No API key"

    payload = {
        "model": member_config["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 2000,
    }

    if HAS_REQUESTS:
        resp = requests.post(
            f"{member_config['base_url']}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    else:
        import subprocess
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", f"{member_config['base_url']}/chat/completions",
             "-H", f"Authorization: Bearer {api_key}",
             "-H", "Content-Type: application/json",
             "-d", json.dumps(payload)],
            capture_output=True, text=True, timeout=60,
        )
        resp = json.loads(result.stdout)
        return resp["choices"][0]["message"]["content"]


def parse_evaluation(response, proposals):
    """Parse LLM response into structured evaluations."""
    # Try strict JSON parse
    try:
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            parsed = json.loads(response[json_start:json_end])
            raw_evals = parsed.get("evaluations", [])
            evals = []
            for e in raw_evals:
                # Normalize: some models use "id", some use "proposal"
                pid = e.get("id") or e.get("proposal") or ""
                vote = (e.get("vote") or "DEFER").upper()
                opinion = e.get("opinion") or e.get("reasoning") or ""
                evals.append({"id": pid, "vote": vote, "opinion": opinion})
            evaluated_ids = {e["id"] for e in evals}
            for p in proposals:
                if p["id"] not in evaluated_ids:
                    evals.append({"id": p["id"], "vote": "DEFER", "opinion": "Not evaluated"})
            return evals
    except json.JSONDecodeError:
        pass

    # Try regex extraction for truncated JSON
    evals = []
    # Match both "id" and "proposal" keys
    pattern = r'\{\s*"(?:id|proposal)"\s*:\s*"(prop-\d+)"\s*,\s*"vote"\s*:\s*"(APPROVE|ESCALATE|DEFER)"'
    matches = re.findall(pattern, response)
    if matches:
        for pid, vote in matches:
            # Try to find opinion near this match
            idx = response.find(pid)
            opinion = ""
            if idx >= 0:
                chunk = response[idx:idx+500]
                op_match = re.search(r'"opinion"\s*:\s*"([^"]*)"', chunk)
                if op_match:
                    opinion = op_match.group(1)
            evals.append({"id": pid, "vote": vote.upper(), "opinion": opinion})
    if evals:
        evaluated_ids = {e["id"] for e in evals}
        for p in proposals:
            if p["id"] not in evaluated_ids:
                evals.append({"id": p["id"], "vote": "DEFER", "opinion": "Not in response"})
        return evals

    # Last resort: infer from text
    for p in proposals:
        pid = p["id"]
        if pid in response:
            idx = response.find(pid)
            nearby = response[idx:idx+500].upper()
            vote = "DEFER"
            if "APPROVE" in nearby:
                vote = "APPROVE"
            elif "ESCALATE" in nearby:
                vote = "ESCALATE"
            opinion = re.sub(r'[{}\[\]"]', '', response[max(0, idx-20):idx+300])[:200]
            evals.append({"id": pid, "vote": vote, "opinion": opinion})
        else:
            evals.append({"id": pid, "vote": "DEFER", "opinion": "Could not parse"})
    return evals


def load_proposals():
    if PROPOSALS_FILE.exists():
        with open(PROPOSALS_FILE) as f:
            return json.load(f)
    return []


def load_budget():
    if BUDGET_FILE.exists():
        with open(BUDGET_FILE) as f:
            return json.load(f)
    return {"sprint": datetime.now(timezone.utc).strftime("%Y-W%W"), "budget": 3.00, "spent": 0.00, "remaining": 3.00, "status": "active"}


def evaluate_proposals(args):
    proposals = load_proposals()
    budget = load_budget()

    if not proposals:
        print("No proposals found. PM needs to generate proposals first.")
        return

    passed = [p for p in proposals if p.get("idea_verifier_status") == "PASS"]
    if not passed:
        print("No proposals passed Idea Verifier.")
        return

    EVALUATIONS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"🏛️  Steering Committee — Evaluating {len(passed)} proposals")
    print(f"{'=' * 70}")
    print(f"Budget: ${budget['budget']:.2f} | Remaining: ${budget['remaining']:.2f}")
    print()

    # Add ROI info to proposals for the committee
    for p in passed:
        cost = p.get("cost_estimate", 0)
        value = p.get("value_per_week", 0)
        if cost > 0 and value > 0:
            p["_roi"] = f"{value/cost:.1f}x"
            p["_payback_weeks"] = f"{cost/value:.1f}" if value > 0 else "N/A"
        else:
            p["_roi"] = "N/A"
            p["_payback_weeks"] = "N/A"

    proposals_text = json.dumps(passed, indent=2)

    # Phase 1: Independent evaluation
    all_evaluations = {}
    budget_ctx = {"budget_remaining": budget["remaining"], "budget_total": budget["budget"]}

    for member_key, member_config in MEMBERS.items():
        system_prompt = SYSTEM_PROMPTS[member_key].format(**budget_ctx)
        print(f"📋 {member_config['name']} ({member_config['model']}) evaluating...")
        try:
            response = call_model(member_config, system_prompt, f"Analyze these improvement proposals:\n\n{proposals_text}")
            parsed = parse_evaluation(response, passed)
            all_evaluations[member_key] = parsed
            print(f"  ✅ Complete")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            all_evaluations[member_key] = [{"id": p["id"], "vote": "DEFER", "opinion": f"Error: {e}"} for p in passed]

        eval_file = EVALUATIONS_DIR / f"{member_key}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}.json"
        with open(eval_file, "w") as f:
            json.dump(all_evaluations[member_key], f, indent=2)

    # Phase 2: Vote tallying
    print(f"\n{'=' * 70}")
    print("📊 Vote Tally & Analysis")
    print(f"{'=' * 70}")

    sprint_plan = {
        "sprint": budget["sprint"],
        "budget": budget["budget"],
        "remaining_budget": budget["remaining"],
        "auto_ship": [],
        "escalate": [],
        "defer": [],
    }

    for proposal in passed:
        pid = proposal["id"]
        votes = {"APPROVE": 0, "ESCALATE": 0, "DEFER": 0}
        opinions = []

        for member_key, member_evals in all_evaluations.items():
            for ev in member_evals:
                if ev.get("id") == pid:
                    vote = ev.get("vote", "DEFER").upper()
                    if vote not in votes:
                        vote = "DEFER"
                    votes[vote] += 1
                    opinions.append({"member": member_key, "vote": vote, "opinion": ev.get("opinion", "")})
                    break

        # Force overrides — escalate the decision but PRESERVE member analysis
        # so the owner sees the actual risk/priority assessment when approving
        is_security = proposal.get("type", "") in SECURITY_TYPES
        is_medium_or_above = proposal.get("cost_estimate", 0) >= 0.50
        forced = False
        if is_security:
            votes = {"APPROVE": 0, "ESCALATE": 3, "DEFER": 0}
            for o in opinions:
                o["vote"] = "ESCALATE"
                # Preserve original opinion, append escalation reason
                original = o.get("opinion", "")
                o["opinion"] = f"{original} [FORCED: security-sensitive type]".strip()
            forced = True
        elif is_medium_or_above:
            votes = {"APPROVE": 0, "ESCALATE": 3, "DEFER": 0}
            for o in opinions:
                o["vote"] = "ESCALATE"
                # Preserve original analysis, append escalation reason
                original = o.get("opinion", "")
                o["opinion"] = f"{original} [FORCED: cost ${proposal.get('cost_estimate', 0):.2f} >= $0.50 medium tier — escalated for {OWNER}'s approval]".strip()
            forced = True

        winner = max(votes, key=votes.get)
        tie = list(votes.values()).count(max(votes.values())) > 1
        if tie:
            winner = "ESCALATE"

        entry = {
            "id": pid,
            "title": proposal["title"],
            "cost_estimate": proposal.get("cost_estimate", 0),
            "value_per_week": proposal.get("value_per_week", 0),
            "roi": proposal.get("_roi", "N/A"),
            "type": proposal.get("type", "unknown"),
            "target_job": proposal.get("target_job", "unknown"),
            "risk": proposal.get("risk", "unknown"),
            "votes": votes,
            "opinions": opinions,
        }

        if winner == "APPROVE":
            cost = proposal.get("cost_estimate", 0)
            if cost <= budget["remaining"]:
                entry["decision"] = "auto-ship"
                sprint_plan["auto_ship"].append(entry)
                sprint_plan["remaining_budget"] -= cost
            else:
                entry["decision"] = "defer"
                entry["defer_reason"] = f"Cost exceeds remaining budget"
                sprint_plan["defer"].append(entry)
        elif winner == "ESCALATE":
            entry["decision"] = "escalate"
            sprint_plan["escalate"].append(entry)
        elif winner == "DEFER":
            # Owner's directive: use the full budget each round.
            # If the item fits within remaining budget, auto-ship it
            # even with a DEFER majority — low ROI != no value.
            cost = proposal.get("cost_estimate", 0)
            if cost <= budget["remaining"]:
                entry["decision"] = "auto-ship"
                entry["note"] = f"DEFER majority but within budget (${cost:.2f} <= ${budget['remaining']:.2f}) — {OWNER}'s directive: use full budget"
                sprint_plan["auto_ship"].append(entry)
                sprint_plan["remaining_budget"] -= cost
            else:
                entry["decision"] = "defer"
                entry["defer_reason"] = f"DEFER majority AND exceeds remaining budget"
                sprint_plan["defer"].append(entry)

        emoji = {"auto-ship": "✅", "escalate": "⚠️", "defer": "⏳"}[entry["decision"]]
        roi_str = f"ROI: {proposal.get('_roi', 'N/A')}" if proposal.get("_roi", "N/A") != "N/A" else "ROI: unquantified"
        print(f"\n{emoji} {proposal['title']} [{proposal.get('risk', '?')}] ${proposal.get('cost_estimate', 0):.2f} | {roi_str}")
        print(f"   Votes: APPROVE:{votes['APPROVE']} ESCALATE:{votes['ESCALATE']} DEFER:{votes['DEFER']} → {entry['decision'].upper()}")
        for op in opinions:
            name = op["member"].replace("_", " ").title()
            print(f"   {name}: {op['vote']}")
            if op["opinion"]:
                print(f"     \"{op['opinion'][:150]}\"")

    # Save sprint plan
    with open(SPRINT_PLAN_FILE, "w") as f:
        json.dump(sprint_plan, f, indent=2)

    # Write committee feedback to pipeline tracker (use sibling script path)
    tracker_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline-tracker.py")
    for proposal in passed:
        pid = proposal["id"]
        for op in opinions:
            if op.get("id") == pid or any(e.get("id") == pid for e in all_evaluations.get(op["member"].split("_")[0] if "_" in op["member"] else op["member"], [])):
                # Find this member's vote for this proposal
                for member_key, member_evals in all_evaluations.items():
                    for ev in member_evals:
                        if ev.get("id") == pid and member_key in op.get("member", ""):
                            try:
                                import subprocess
                                subprocess.run(
                                    [sys.executable, tracker_script, "add-feedback",
                                     "--id", pid,
                                     "--member", member_key,
                                     "--vote", ev.get("vote", "DEFER"),
                                     "--reason", ev.get("opinion", "No reason given")[:200]],
                                    capture_output=True, timeout=10,
                                )
                            except Exception:
                                pass  # Non-critical — don't fail the committee if tracker fails

    # Summary
    auto_cost = sum(e.get("cost_estimate", 0) for e in sprint_plan["auto_ship"])
    print(f"\n{'=' * 70}")
    print(f"📋 Sprint Plan — {sprint_plan['sprint']}")
    print(f"{'=' * 70}")
    print(f"Budget: ${sprint_plan['budget']:.2f}")
    print(f"Auto-ship cost: ${auto_cost:.2f}")
    print(f"Remaining: ${sprint_plan['remaining_budget']:.2f}")
    print(f"\n✅ Auto-ship: {len(sprint_plan['auto_ship'])} items")
    print(f"⚠️  Escalate: {len(sprint_plan['escalate'])} items")
    print(f"⏳ Defer: {len(sprint_plan['defer'])} items")

    return sprint_plan


def show_status(args):
    budget = load_budget()
    print(f"📊 Sprint Status — {budget['sprint']}")
    print(f"{'=' * 50}")
    print(f"Budget: ${budget['budget']:.2f}")
    print(f"Spent: ${budget['spent']:.2f}")
    print(f"Remaining: ${budget['remaining']:.2f}")


# ─── System Prompts ──────────────────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "budget_analyst": """You are the Budget Analyst on a Steering Committee for a self-improving automation system.

For each proposal, analyze: Is the cost realistic? Is the value credible? What's the ROI (value_per_week / cost_estimate)? What's the opportunity cost?

Current budget: ${budget_remaining:.2f} remaining of ${budget_total:.2f}

Be opinionated. Challenge inflated value estimates.

Vote APPROVE (good value, fits budget), ESCALATE (value unclear, needs human judgment), or DEFER (poor value).

JSON format: {{"evaluations": [{{"id": "prop-001", "vote": "APPROVE", "opinion": "your assessment"}}]}}""",

    "risk_assessor": """You are the Risk Assessor on a Steering Committee for a self-improving automation system.

For each proposal, evaluate: blast radius (one script or cascading?), security implications, failure mode (worst case?), new dependencies, rollback difficulty.

Security-sensitive types (firewall_rule, dns_config, ssh_key, certificate, vlan_change, permission_change) MUST be voted ESCALATE.

Be the skeptic. Catch what others miss.

Vote APPROVE (low risk, safe), ESCALATE (needs human review), or DEFER (too risky).

JSON format: {{"evaluations": [{{"id": "prop-001", "vote": "APPROVE", "opinion": "your risk assessment"}}]}}""",

    "priority_arbitrator": """You are the Priority Arbitrator on a Steering Committee for a self-improving automation system.

For each proposal, evaluate: impact (how much does this improve things?), timing (urgent or nice-to-have?), leverage (does this unlock other improvements?), ROI (value_per_week / cost_estimate), opportunity cost (what are we NOT building?).

Current budget: ${budget_remaining:.2f} remaining. Pack the sprint wisely.

Think like a product manager. What moves the needle?

Vote APPROVE (high impact, good ROI), ESCALATE (impact unclear, human should decide), or DEFER (low impact, save budget).

JSON format: {{"evaluations": [{{"id": "prop-001", "vote": "APPROVE", "opinion": "your priority assessment"}}]}}""",
}


def main():
    parser = argparse.ArgumentParser(description="Steering Committee")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("evaluate", help="Run 3-member evaluation + vote")
    subparsers.add_parser("status", help="Show current sprint status")
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"evaluate": evaluate_proposals, "status": show_status}[args.command](args)


if __name__ == "__main__":
    main()
