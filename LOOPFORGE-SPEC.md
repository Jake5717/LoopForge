---
name: loop-engineer
description: > 
  Self-improving Kaizen pipeline: PM generates 3-5 proposals, Steering Committee
  classifies and packs sprint, Idea Verifier checks research, Code Writer implements
  auto-shipped items, Code Verifier reviews. 4 models + Steering Committee.
  $3/week budget. USE THE FULL BUDGET — low ROI items within budget still ship.
  Escalate medium/major to [USER] WITH full risk/priority analysis.
  Idea Verifier uses Gemini 2.5 Flash (not Sonnet — too expensive).
tags: [automation, self-improvement, loop-engineer, kaizen]
version: 7.0.0
---

# Loop Engineer — Kaizen Pipeline v6

## Overview

A 6-step pipeline where each step uses a different model for genuine independence. The Steering Committee classifies proposals and packs a weekly sprint with a $3 budget. Minor items auto-ship; medium/major items require [USER]'s approval. The system improves all 14+ cron jobs on a weekly cycle.

**Core principle:** PM researches multiple improvements. Steering Committee decides what fits the budget. Idea Verifier checks quality. Code Writer implements approved plans. Code Verifier reviews. Each model has different training, different blind spots, different tendencies.

## Pipeline Flow

```
10:00 AM  PM (V2.5 Pro)               Research → 3-5 proposals with cost estimates
10:15 AM  Idea Verifier (Gemini Flash)  "Is this the right thing to build?"
10:20 AM  Steering Committee (V2.5 Pro)  Classify, pack sprint, route to auto-ship or approval
   ...    [If medium/major: wait for [USER]'s approval via approval mechanism]
10:30 AM  Code Writer (Claude Code)     Implements auto-shipped items only
10:45 AM  Code Verifier (GPT-4o)        "Does this code work? Any bugs?"
11:00 AM  Engineering Phase (V2.5 Pro)  Commit + changelog + state updates
After     Approval Processor (cron)     Applies [USER]-approved items when he responds
```

**If Idea Verifier fails a proposal:** That proposal is rejected. Failure feeds back to backlog.
**If Code Verifier fails:** Change reverts. Failure feeds back to backlog.
**If Steering Committee defers:** Proposal goes to next sprint's backlog.
**Engineering Phase:** Runs after Code Verifier passes. Commits changes and updates state files.
**Approval Processor:** Cron job (every 15m) that applies items [USER] approves.

## The 4 Models + Steering Committee

| Step | Model | Provider | Why This Model |
|------|-------|----------|---------------|
| PM | V2.5 Pro | Xiaomi | Cheap, good at research synthesis |
| Steering Committee | 3 cheap models (parallel) | Mixed | Independent perspectives at minimal cost |
| Idea Verifier | Gemini 2.5 Flash | OpenRouter | Cheap, fast, sufficient for gap analysis |
| Code Writer | Claude Code | Anthropic CLI | Built for coding — has tools, terminal, tests |
| Code Verifier | GPT-4o | OpenRouter | Different model family = genuine independence |

**Steering Committee members (all content-agnostic — evaluate any proposal type):**

| Member | Model | Evaluates |
|--------|-------|-----------|
| Budget Analyst | MiMo 2.5 | Cost realism, value credibility, ROI, opportunity cost |
| Risk Assessor | Gemini 2.5 Flash | Blast radius, security, failure modes, dependencies |
| Priority Arbitrator | GPT-4o Mini | Impact, timing, leverage, ROI, opportunity cost |

Each member thinks independently and provides genuine analysis. Majority vote decides. Security-sensitive and medium-tier items force-escalate. Cost: ~$0.002 per classification.

## Sprint Budget

- Default: **$3/week** (configurable in `~/.hermes/data/loop-engineer/sprint-budget.json`)
- Budget covers: all model costs for the pipeline
- Auto-shipped items consume budget immediately
- Escalated items consume budget when [USER] approves
- If budget runs out, remaining proposals defer to next sprint

### ⚠️ [USER]'s Directive: USE THE FULL BUDGET (2026-06-14)

**The committee should spend the entire $3/week budget each round.** Items with low ROI should still be auto-shipped if they fit within the remaining budget. Low ROI ≠ no value. Only defer if the cost actually exceeds the remaining budget.

The previous behavior of deferring items purely because of low ROI (e.g., 0.7x) left money on the table. The committee's job is to maximize improvement per dollar, not to hoard budget.

In `steering-committee.py`, when the majority vote is DEFER but the item fits within the remaining budget, it auto-ships with a note: `"DEFER majority but within budget — [USER]'s directive: use full budget"`.

### Cost Tiers

| Tier | Cost Estimate | Decision | Example |
|------|--------------|----------|---------|
| Minor | < $0.50 | Auto-ship (if meets criteria) | New output field, better error message, log format |
| Medium | $0.50-1.50 | Escalate to [USER] | New detection logic, changed thresholds |
| Major | > $1.50 | Escalate to [USER], may break down | New script, new integration, architecture change |

### Auto-Ship Criteria (ALL must be true)

1. Cost estimate < $0.50 (minor tier)
2. Idea Verifier rated research STRONG or ADEQUATE
3. Change affects only the target script (no cross-cutting)
4. NOT a security-sensitive type (firewall, DNS, SSH, certs, VLAN, permissions)
5. NOT modifying another cron job's behavior
6. NOT modifying the approval mechanism itself
7. NOT adding new external dependencies
8. NOT changing output format that other jobs consume

If ANY criterion fails, the item is escalated to [USER] even if it's minor.

### Security-Sensitive Changes (ALWAYS escalate)

These require [USER]'s explicit approval regardless of tier:
- Firewall rule modifications
- DNS configuration changes
- SSH key/credential updates
- SSL/TLS certificate changes
- VLAN reconfigurations
- User permission/role changes
- Automated deployment of security policies

## Step 1: PM Research (V2.5 Pro)

**Mission:** Generate 3-5 improvement proposals with cost estimates.

### Selection

Read `~/.hermes/data/loop-engineer/backlog.md` — pick highest-priority items.
Read `~/.hermes/data/loop-engineer/cycle-history.md` — avoid recently improved jobs.
Generate 3-5 proposals (not just one).

### Full Job Inventory

| # | Job | Type | Domain |
|---|-----|------|--------|
| 1 | ic-containers.py | Script | Docker/SRE |
| 2 | ic-resources.py | Script | Capacity planning |
| 3 | ic-errors.py | Script | Observability |
| 4 | network-guard.py | Script | Network security |
| 5 | Network Guard Analysis | Agent | Threat intelligence |
| 6 | IC Morning Briefing | Agent | SRE |
| 7 | Ward | Agent | Governance |
| 8 | Scribe | Agent | Knowledge mgmt |
| 9 | LinkedIn Monitor | Script+Agent | Job matching |
| 10 | Discord Thread Renamer | Script | Community mgmt |
| 11 | Hermes & AI News | Agent | Research |
| 12 | Guyana News | Agent | Research |
| 13 | Git Backup | Agent | DevOps |
| 14 | Loop Engineer (this system) | Meta | Self-improvement |

### Research Protocol

Do NOT just do 3 web searches. Research systematically:

1. Read the current job — what does it do today?
2. Check backlog.md for specific issues reported
3. Search for expert sources:
   - GitHub repos with high stars in this domain
   - Official documentation for the tools involved
   - Reddit/HN discussions from practitioners (not tutorials)
   - Blog posts from known experts
4. Read 3-5 sources in depth (not just search descriptions)
5. Synthesize: what does a master practitioner do that we don't?

### Output

Write proposals to `~/.hermes/data/loop-engineer/current-proposals.json`:

```json
[
  {
    "id": "prop-001",
    "title": "Brief title of the improvement",
    "description": "What the improvement does and why",
    "cost_estimate": 0.45,
    "value_estimate": "Quantified value — be specific: 'saves ~10 min/week' not 'improves monitoring'",
    "value_per_week": 0.80,
    "risk": "low|medium|high",
    "type": "improvement|security|config",
    "target_job": "script-name.py",
    "implementation_plan": "Concrete steps to implement",
    "sources_consulted": ["url1", "url2"],
    "expert_finding": "What experts do that we don't"
  }
]
```

**Value estimation is mandatory.** Every proposal MUST include `value_per_week`. The Steering Committee uses this for ROI analysis. If you can't quantify precisely, say so honestly — but always attempt a number.

## Step 1.5: Steering Committee (3 cheap models)

**Mission:** Classify proposals, evaluate ROI, pack the sprint, route to auto-ship or approval queue.

### ⚠️ Required Pre-Step: Propagate Idea Verifier Status

The steering committee script filters proposals by `idea_verifier_status == "PASS"`, but the Idea Verifier writes to a **separate file** (`idea-verdicts.json`). Before running the committee, you MUST merge the verdict status into `current-proposals.json`:

```python
import json
with open('current-proposals.json') as f:
    proposals = json.load(f)
with open('idea-verdicts.json') as f:
    verdicts = json.load(f)
verdict_map = {v['id']: v['status'] for v in verdicts}
for p in proposals:
    if p['id'] in verdict_map:
        p['idea_verifier_status'] = verdict_map[p['id']]
with open('current-proposals.json', 'w') as f:
    json.dump(proposals, f, indent=2)
```

Also ensure `sprint-budget.json` exists (the script creates a default if missing, but explicit is better).

### Members

| Member | Model | What They Argue About |
|--------|-------|----------------------|
| Budget Analyst | MiMo 2.5 | "Is this worth the cost? Is the value estimate credible?" |
| Risk Assessor | Gemini 2.5 Flash | "What could go wrong? Blast radius, security, dependencies." |
| Priority Arbitrator | GPT-4o Mini | "Is this the best use of our budget this sprint?" |

All members are content-agnostic — they evaluate any proposal type (Docker, LinkedIn, firewall, meal planning) through their role's lens.

### ROI Analysis

The PM includes `value_per_week` in each proposal. The committee uses this to evaluate ROI:

- **ROI** = value_per_week / cost_estimate
- **Payback period** = cost_estimate / value_per_week (weeks to break even)
- Budget Analyst challenges inflated value estimates
- Priority Arbitrator uses ROI to rank proposals

### Process

1. Read proposals from `current-proposals.json` (each includes `value_per_week`)
2. Calculate ROI for each proposal
3. Each member independently evaluates all proposals
4. Majority vote decides: auto-ship / escalate / defer
5. Security-sensitive and medium-tier (≥ $0.50) items force-escalate (but preserve member analysis)
6. If majority is DEFER but item fits in remaining budget → auto-ship ([USER]'s directive: use full budget)
7. Generate sprint plan to `sprint-plan.json`

### Scripts

```bash
python3 ~/.hermes/scripts/steering-committee.py evaluate
python3 ~/.hermes/scripts/steering-committee.py status
```

**Note:** There is NO `auto-ship` subcommand. The script only has `evaluate` and `status`. Auto-ship processing is done by the facilitator (see Facilitator Workflow below).

### Facilitator Workflow (Post-Committee)

After the committee evaluates, a facilitator agent processes the results. Full details in `references/steering-committee-facilitator.md`.

1. **Auto-shipped items:** Create an approval via `approval-manager.py propose`, then immediately `approval-manager.py approve` with `--approved-by "steering-committee"`. This records the approval in the system.
2. **Escalated items:** Create an approval via `approval-manager.py propose` with `--proposed-by "steering-committee"`. Leave as pending for [USER].
3. **Deferred items:** Add to `improvement-backlog.md` under the appropriate job section with a note: `⏳ DEFERRED (YYYY-WNN): <title> [prop-NNN] — ROI X.Xx, $N.NN. <vote summary>. Next sprint candidate.`
4. **Update budget:** Set `spent` and `remaining` in `sprint-budget.json` to reflect auto-shipped costs.
5. **Send summary to [USER]:** Report auto-shipped (why approved), escalated (vote breakdown + expiration), deferred (why), and budget status.

## Step 2: Idea Verifier (Gemini 2.5 Flash)

**Mission:** Evaluate the research and recommendation BEFORE any code is written.

Read the proposals. Be analytical and critical.

### What to Check

1. **Research Quality:** Did the PM consult real expert sources? Or just quick searches? Rate: STRONG / ADEQUATE / WEAK
2. **Gap Analysis:** Are the identified gaps accurate? Read the actual script/job to verify.
3. **Recommendation:** Is this the highest-impact improvement? Are there better approaches missed?
4. **Implementation Plan:** Is it concrete enough for a coder to follow?

### Decision

Write verdicts to `~/.hermes/data/loop-engineer/idea-verdicts.json`:

```json
[
  {
    "id": "prop-001",
    "status": "PASS",
    "research_quality": "STRONG",
    "feedback": "Solid research, concrete plan"
  }
]
```

**If FAIL:** That proposal is rejected. The failure goes to the backlog — next cycle's PM sees what went wrong.

## Step 3: Code Writer (Claude Code)

**Mission:** Read the sprint plan. Implement ONLY auto-shipped items. Use Claude Code for actual coding.

### Process

1. Check `~/.hermes/data/loop-engineer/sprint-plan.json` — only implement items in the `auto_ship` list
2. For each auto-shipped item, read the proposal and implementation plan
3. Invoke Claude Code:

```bash
claude -p "Read the proposal at ~/.hermes/data/loop-engineer/current-proposals.json (find proposal with ID: <id>). Implement the recommended improvement. Preserve existing output format. Add comments explaining new logic. Do NOT rewrite the entire file — make the ONE specific change described in the implementation plan." \
  --allowedTools "Read,Edit,Write,Bash" \
  --max-turns 15 \
  --max-budget-usd 0.50 \
  --bare
```

4. Verify Claude Code's work — did it actually change? Does it match the proposal?
5. Record actual cost: `python3 ~/.hermes/scripts/steering-committee.py apply-cost <id> <actual_cost>`

**DO NOT implement escalated or deferred items.** Those wait for [USER]'s approval or next sprint.

### Fallback: Direct Implementation (when Claude Code is unavailable)

If Claude Code is not logged in, missing, or errors on invocation, implement changes directly using the `patch` tool for targeted edits and `write_file` for new files. Steps:

1. `cp target.py target.py.bak.$(date +%Y%m%d)` — backup first
2. Read the target script fully to understand its structure
3. Use `patch` (mode='replace') for each specific change — do NOT rewrite entire files
4. Verify with `python3 -c "import py_compile; py_compile.compile('target.py', doraise=True)"` for syntax
5. Verify with `python3 -c "import ast; ..."` to check new functions exist in the AST
6. Run the script to verify it executes without crashing
7. Run targeted unit tests if the change adds new logic branches

This fallback is equivalent to Claude Code for minor/medium changes. For complex multi-file refactors, defer and report the blocker.

## Step 4: Code Verifier (GPT-4o)

**Mission:** Adversarial code review on a completely different model family.

### What to Check

1. **Technical:** Syntax, edge cases, regressions, error handling
2. **Scope:** Does code match the proposal? No scope creep?
3. **Quality:** Readable, well-commented, no security issues?
4. **Proposal compliance:** Was exactly the proposed change implemented?

### Decision

Write verdicts to `~/.hermes/data/loop-engineer/code-verdicts.json`:

```json
[
  {
    "id": "prop-001",
    "status": "PASS",
    "feedback": "Clean implementation, no issues"
  }
]
```

**PASS:** Change proceeds to Engineering Phase.
**FAIL (code review found bugs):** Change reverts. Failure feeds back to backlog.
**FAILED (job crashed / technical failure):** The Code Verifier cron job may fail before producing a review (API error, token limit, provider outage). This is NOT a code review failure — the code was never reviewed. The Engineering Phase must perform manual verification instead of reverting. See Engineering Phase step 1.

## Step 5: Engineering Phase (V2.5 Pro — Post-Verification)

**Mission:** After Code Verifier passes, commit the change and update all state files.

### Process

1. **Verify verdicts** — confirm Code Verifier passed for each implemented item. If the Code Verifier cron job failed technically (crash, API error — check job status for "(FAILED)" marker), perform manual verification instead of reverting:
   ```python
   # AST syntax check
   python3 -c "import ast; ast.parse(open('target.py').read())"
   # Function existence check
   python3 -c "import ast; tree=ast.parse(open('target.py').read()); print([n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])"
   # Runtime check (will fail on SSH but catches import/syntax errors)
   python3 target.py
   ```
   Record the manual verification result in the changelog and cycle history. Note: "Code Verifier: FAILED (job crash) — manual verification PASS".
2. **Commit** — git commit (or snapshot to baselines if not in git)
3. **Update changelog** — what/why/risk/undo, which models
4. **Update cycle history** — full cycle record
5. **Update backlog** — mark done, add new items
6. **Update expert directory** — new sources discovered

### Commit Message Format
```
loop-engineer: [brief description]

Auto-shipped: yes/no
Research: PM's source summary
Idea Verifier: PASS (Gemini 2.5 Flash)
Steering Committee: auto-ship / escalated / deferred
Code Writer: Claude Code
Code Verifier: PASS (GPT-4o)
Approved by: [USER] (if escalated) / auto-shipped
```

## Approval Mechanism

The approval mechanism is an asynchronous human-in-the-loop system. No job ever "waits" for [USER] — proposals are saved, notifications sent, and jobs exit.

### Architecture

```
Agent runs → encounters change → writes proposal to ~/.hermes/approvals/pending/
  → Sends Discord/Telegram notification to [USER]
  → Job exits (no waiting)

[USER] approves/denies when available → response captured in pending store

Approval Processor cron (every 15m) → finds approved items → applies them
```

### [USER]'s Interaction Pattern

[USER] says "Approve apr-XXXXXX" (short ID). The agent should:
1. Find the matching file in `~/.hermes/approvals/pending/` (files use full IDs like `apr-YYYYMMDD-HHMM-XXXXXX.json`)
2. Read it to confirm what the approval is for
3. Run `python3 ~/.hermes/scripts/approval-manager.py approve --id <full-id> --note "Approved by [USER]"`
4. Report back to [USER] what was approved

[USER] can also say "Deny apr-XXXXXX" — use `approval-manager.py deny --id <full-id> --reason "..."`.

### Directory Structure

```
~/.hermes/approvals/
  pending/     # Awaiting [USER]'s approval
  approved/    # Approved, waiting to be processed
  denied/      # Denied by [USER]
  expired/     # Timed out (no response)
  applied/     # Successfully applied
  rollbacks/   # Rollback snapshots
```

### Script: `approval-manager.py`

```bash
# Propose a change
python3 ~/.hermes/scripts/approval-manager.py propose \
  --title "Update firewall rule" \
  --description "Add rate limiting to WAN_IN" \
  --risk medium \
  --type firewall_rule \
  --proposed-by "loop-engineer"

# Check status
python3 ~/.hermes/scripts/approval-manager.py status

# Approve (called by agent when [USER] responds)
python3 ~/.hermes/scripts/approval-manager.py approve --id apr-XXXXXX --note "Looks good"

# Deny (called by agent when [USER] responds)
python3 ~/.hermes/scripts/approval-manager.py deny --id apr-XXXXXX --reason "Wait until..."

# Generate digest
python3 ~/.hermes/scripts/approval-manager.py digest
```

### Risk-Based Expiration

| Risk | Expiration | Example |
|------|-----------|---------|
| Critical | 24 hours | Data loss risk |
| High | 48 hours | Security changes |
| Medium | 72 hours | Feature changes |
| Low | 7 days | Cosmetic fixes |

### Rollback Window

Every approved change has a rollback window of **3 runs** (configurable). The agent captures a baseline before applying the change. If the change causes problems within the window, it can be reverted.

## Dynamic Backlog

`backlog.md` is populated by real problems, not manual entries.

**How items get added:**
- [USER] gives feedback → `python3 ~/.hermes/scripts/loop-engineer-feedback.py --feedback "..."`
- Incident occurs → `--incident /path/to/incident.md`
- Verifier rejects → `--verifier "..."`
- System identifies own gap → `--system "..."`

**The PM reads backlog.md every cycle** and prioritizes backlog items over generic improvements. Real problems first.

## Feedback Loops

The pipeline learns from its own outcomes. Three feedback mechanisms:

**CLI reference:** See `references/pipeline-tracker-cli.md` for exact command syntax and arg types.

### 1. Budget Actuals (estimate vs actual)

After Code Writer implements, it records actual cost vs estimate:
```bash
python3 ~/.hermes/scripts/pipeline-tracker.py record-cost --id prop-001 --estimated 0.40 --actual 0.45
```

The tracker learns: "PM consistently underestimates by ~15%." This context feeds back to the PM for better estimation.

### 2. Outcome Measurement (claimed vs real impact)

Monthly verification checks whether shipped improvements had their claimed impact:
```bash
python3 ~/.hermes/scripts/pipeline-tracker.py record-outcome --id prop-001 --claimed 0.80 --measured 0.60 --notes "Saves ~7 min/week, not 10"
```

If the PM claims "saves 10 min/week" and the reality is 7 min/week, the PM learns to estimate more conservatively.

### 3. Committee Feedback to PM

The facilitator writes committee feedback directly to `pm-context.json` (fields: `committee_feedback_summary`, `instructions`, `known_issues`). Individual member evaluations live in `committee-evaluations/<member>-<timestamp>.json`.

Before the PM generates new proposals, it reads the context file at `~/.hermes/data/loop-engineer/pm-context.json`. The PM sees: "Last cycle, 2 proposals were deferred because 'low impact.' Avoid repeating this pattern."

**Note:** `pipeline-tracker.py add-feedback` and `feedback-for-pm` exist but are not used by the current facilitator workflow. The facilitator writes directly to pm-context.json instead.

### Reports

```bash
python3 ~/.hermes/scripts/pipeline-tracker.py cost-report      # Estimate vs actual analysis
python3 ~/.hermes/scripts/pipeline-tracker.py outcome-report   # Claimed vs measured impact
python3 ~/.hermes/scripts/pipeline-tracker.py feedback-for-pm  # Committee feedback summary (currently unused — feedback goes to pm-context.json directly)
python3 ~/.hermes/scripts/pipeline-tracker.py pm-context       # Generate PM context file
```

**Note:** `feedback-for-pm` currently returns empty because the facilitator writes to `pm-context.json` directly. To see feedback, read `pm-context.json` or check `committee-evaluations/` for individual member evaluations.

## State Files

All in `~/.hermes/data/loop-engineer/`:

| File | Purpose |
|------|---------|
| `backlog.md` | Dynamic prioritized list of improvements needed |
| `current-proposals.json` | PM's 3-5 proposals (current cycle) |
| `idea-verdicts.json` | Idea Verifier's verdicts on each proposal |
| `sprint-plan.json` | Steering Committee's sprint plan |
| `code-verdicts.json` | Code Verifier's verdicts |
| `sprint-budget.json` | Budget tracking per sprint |
| `cost-actuals.json` | Estimate vs actual cost data |
| `outcomes.json` | Claimed vs measured impact data |
| `committee-evaluations/` | Per-member evaluation files (e.g. `risk_assessor-20260614-1722.json`) — individual votes + opinions |
| `pm-context.json` | Context file for PM's next cycle |
| `cycle-history.md` | Record of every cycle |
| `changelog.md` | Every change committed |
| `expert-directory.json` | Domain experts discovered |
| `script-baselines/` | Snapshots before modification |

## Feedback Ingestion

Script: `~/.hermes/scripts/loop-engineer-feedback.py`

```bash
python3 ~/.hermes/scripts/loop-engineer-feedback.py --feedback "ic-containers.py gave wrong alert"
python3 ~/.hermes/scripts/loop-engineer-feedback.py --verifier "Research only did web searches, no GitHub repos"
python3 ~/.hermes/scripts/loop-engineer-feedback.py --system "Improver prompt too vague"
```

## Self-Improvement

Job #14 in the rotation is the Loop Engineer itself. Every 4th cycle, the PM reviews and improves:
- The PM prompt (is research protocol working?)
- The Idea Verifier prompt (is it catching real issues?)
- The Steering Committee logic (is classification accurate?)
- The Code Writer prompt (is Claude Code getting good instructions?)
- The Code Verifier prompt (is it finding real bugs?)
- The overall process (what's confusing, what's missing?)

## Cost

~$1.50-2.50 per weekly cycle (with 3-5 proposals). ~$80-130/year.

Breakdown: PM (V2.5 Pro) ~$0.25, Steering Committee (V2.5 Pro) ~$0.15, Idea Verifier (Gemini Flash) ~$0.05, Code Writer (Claude Code) ~$0.60, Code Verifier (GPT-4o) ~$0.25.

Sprint budget: $3/week covers all pipeline costs plus auto-shipped improvements.

### Idea Verifier Model Swap (2026-06-14)

The Idea Verifier was originally `anthropic/claude-sonnet-4` via OpenRouter. This burned ~$5 over 2 days because:
- Sonnet made 16 API calls per run with 65K-92K input tokens each (~1.2M total)
- Two stale "Meta" jobs also used Sonnet on Jun 12 (39 calls, ~4M tokens)
- Total: ~55 Sonnet calls through OpenRouter

Swapped to `google/gemini-2.5-flash` via OpenRouter. The gap analysis and research quality checks it performs don't require Sonnet-level reasoning. Cost dropped from ~$0.80/run to ~$0.05/run.

**Cron job ID:** `<CRON_JOB_ID>` — model set to `google/gemini-2.5-flash`, provider `openrouter`.

See `references/idea-verifier-cost-incident.md` for the full incident timeline and root cause analysis.

## Safety

- Multiple improvements per cycle (budget-limited, not one-at-a-time)
- Idea verification BEFORE coding (saves tokens on bad ideas)
- Steering Committee classifies BEFORE coding (budget-aware)
- Each step checks previous step's output
- Failures feed back to backlog (system learns from mistakes)
- Committee feedback feeds back to PM (PM learns from past decisions)
- Budget actuals tracked (estimates improve over time)
- Outcome measurement (PM learns if value claims were accurate)
- [USER] approves medium/major items via async approval mechanism
- Security-sensitive changes ALWAYS require [USER]'s explicit approval
- Rollback window of 3 runs for all changes
- Asynchronous approval — no job waits for [USER], proposals expire safely

## Pitfalls

- **Don't describe changes without implementing them.** [USER]: "I thought we already upgraded to a two model process. I want that. Do that now." If approved, implement immediately.
- **Don't default to one job.** The system improves ALL 14+ jobs, not just ic-containers.py. [USER]: "you keep talking about containers — that's just 1 cron job out of many."
- **Don't build governance before running a cycle.** We built Advisory Board, intake process, tiered approval before running a single successful pilot. Strip to basics first, prove the pattern, then add complexity.
- **Don't skip the improvement brief.** The PM's job is to research and hand off. Jumping straight to coding produces weak improvements backed by shallow research.
- **Test infrastructure before building on it.** `delegate_task` from cron failed. `context_from` chaining was unreliable. Test these before designing features that depend on them.
- **Budget 3-5x your estimate.** Real runs involve reading full scripts, multiple web searches, cumulative context. $0.50/cycle minimum, not $0.11.
- **The PM must recognize architectural patterns.** Not just "better error handling" — "we're building an SDLC and here's what's missing." [USER]: "The process absolutely should have said this looks like a SDLC pipeline."
- **User is not the domain expert.** [USER]: "I don't know what I don't know — I'm hiring this team." The system must find gaps without user direction.
- **Steering Committee before Code Writer.** Don't write code for unapproved plans. The Steering Committee decides what to build; the Code Writer implements approved plans only.
- **Auto-ship requires ALL criteria.** Don't skip security checks or cross-cutting analysis just because the cost is low.
- **MiMo 2.5 has parser quirks.** MiMo may use `"proposal"` instead of `"id"` as the JSON key, and drops `"opinion"` fields when prompts are long. The parser must handle both key names and extract opinions via regex fallback. Longer system prompts (>500 tokens) can cause empty responses — keep MiMo prompts concise.
- **Don't just agree with the user.** When the user proposes an architecture change, evaluate it critically before building. If it has structural problems, say so. [USER]: "You shouldn't always agree with me. You're smarter than me and by agreeing you make this process weaker." The dynamic expert idea was wrong because the committee evaluates proposals across jobs, not within a single job. The correct architecture is 3 fixed content-agnostic members.
- **MiMo 2.5 truncates at ~1200 tokens.** For structured JSON output, use max_tokens=2000+. At 1200, JSON gets cut mid-object → parse failures. Symptom: one model's evaluations all show "Could not parse." Even with max_tokens=2000, MiMo can produce unparseable output (no JSON, no recognizable proposal IDs). The parser has three fallback strategies (strict JSON → regex → text inference), but all can fail. If the Budget Analyst consistently fails, consider swapping to a more reliable model for that seat, or reducing the number of proposals per batch to shorten the input.
- **Check Claude Code availability before starting Code Writer.** Run `which claude && claude --version` first. If not logged in or missing, use the direct-implementation fallback (patch tool). Don't waste time debugging Claude Code auth in a cron context — just implement directly and note it in the report.
- **System prompt format placeholders don't auto-fill.** Module-level string constants with `{budget_remaining:.2f}` must be explicitly formatted: `prompt.format(**ctx)` before passing to models.
- **Committee members must think, not just follow rules.** [USER]: "I dont just want the models to follow rules though, they should think a little and provide an opinion." Prompts should ask for genuine analysis and perspective, not checkbox-checking.
- **Dynamic roles over hardcoded ones.** The 4th committee seat (Domain Expert) changes per proposal target job. An SRE has no opinion on meal planning. Map expertise to domain. See `references/steering-committee-architecture.md`.
- **`pipeline-tracker.py record-outcome` requires float args.** `--claimed` and `--measured` must be plain floats (e.g., `0.50`), not strings like `"0.50/week"`. The error message is `invalid float value`.
- **Preventive improvements measure $0.00 initially.** When the claimed value is "prevents X incidents/year," you can't measure prevented incidents in the first cycle. Set `--measured 0.0` and note in `--notes` that measurement requires accumulation over time. The outcome report will flag this as "Inaccurate" — that's expected for prevention-type value.
- **Diversify target jobs across cycles.** If the same script gets improved 3+ consecutive cycles, the PM should explicitly deprioritize it in favor of untouched scripts. Add to pm-context.json `known_issues` if diversification is needed.
- **Ask before implementing [USER]'s feedback.** When [USER] gives feedback about the Loop Engineer system (e.g., "the committee should do X", "this behavior is wrong"), ask: "Want me to implement this now, or write it to the backlog?" Don't immediately start coding. Some feedback is quick to fix; other items should go through the normal pipeline. [USER] explicitly corrected this: "you didn't need to implement those last fixes. Instead next time ask do you want me to work on this now, or do you want me to write it to the backlog?"
- **Force-escalation must preserve member analysis.** When `steering-committee.py` force-escalates an item (security-sensitive or ≥ $0.50 medium tier), it must NOT overwrite the Risk Assessor and Priority Arbitrator's original opinions with a one-liner. [USER] needs to see the actual risk and priority assessment when deciding whether to approve. The fix: change the vote to ESCALATE but append `[FORCED: reason]` to the existing opinion instead of replacing it. This was a real bug in cycle 2 — all three members just said "forced escalate" and [USER] had to evaluate the risk himself.
- **[USER]'s escalation analysis directive (2026-06-14):** Even on force-escalated items, committee members MUST provide their full analysis. Risk Assessor must assess blast radius, security, failure modes. Priority Arbitrator must evaluate impact, timing, opportunity cost. A one-line "over budget" note is not enough — [USER] needs the real analysis to make an informed approval decision.
