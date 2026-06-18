# Loop Engineer — Governance Model

## Intake Process

Users submit requests via natural conversation. Hermes routes them to `~/.hermes/data/loop-engineer/requests.md`.

**Request types:**
| Type | Example | Flow |
|------|---------|------|
| Feature request | "I want error scanning to check Docker logs" | PM evaluates → Advisory Board → [USER] approves |
| Bug report | "ic-containers.py gave a false alert" | PM investigates → proposes fix → Verifier checks → [USER] approves |
| New product | "I want email monitoring" | PM researches scope → Advisory Board reviews → [USER] approves → Engineering builds |

**Key principle:** User requests and autonomous improvements go in the same backlog, prioritized together. The PM decides which to do first based on impact and effort.

## Tiered Approval

| Tier | What Changes | [USER]'s Role | Example |
|------|-------------|-------------|---------|
| Tier 1: Auto-ship | Small, low-risk | Informed after the fact | New output field, better error message, log format |
| Tier 2: Approve | Medium changes | Advisory Board recommends, [USER] decides | New detection logic, new host checks, changed thresholds |
| Tier 3: Must approve | Major rewrites, new agents | Blocks until explicit approval | New cron job, new script architecture, new integration |

## Changelog

Every committed improvement includes an entry in `~/.hermes/data/loop-engineer/changelog.md`:
- What changed (plain English)
- Why it changed (research finding)
- Risk (what could go wrong)
- Undo (revert command)
- Tier (1/2/3)
- Approved by ([USER] / auto-shipped)
- Verifier (PASS/FAIL)
- Advisory Board (X/4 recommended)

## Steering Committee Summary

Weekly summary delivered to [USER]:
- What was proposed and what experts said
- What was implemented
- What's in the backlog
- Token spend and cost
- Any items needing [USER]'s decision

## Approval Workflow

1. Improver proposes improvement + Advisory Board debates
2. Verifier (different model) reviews quality
3. Steering Summary delivered to [USER]
4. [USER] says "ship it" / "skip" / "reprioritize" / "shut it down"
5. Engineering Phase implements what [USER] approved
6. Changelog updated, state files updated

## Key Insight (from [USER])

[USER] is not a technical expert on Docker monitoring, network security, etc. He shouldn't evaluate technical recommendations. The Advisory Board gives him a verdict he can trust: "3/4 experts recommend this, SRE says high value, risk expert says low risk." [USER]'s decision becomes "agree with the experts" or "override with reason."
