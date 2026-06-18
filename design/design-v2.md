# Loop Engineer — Design Document v2

**Date:** 2026-06-12
**Status:** Revised after meta-loop PM review + independent verification
**Authors:** [USER] + Hermes (v1), PM research + Loop Engineer revision (v2), Meta-loop engineering (v3)
**Previous version:** design-v2.md

## What Changed from v1

| Area | v1 | v2 | Why |
|------|----|----|-----|
| Agent roles | 3 agents (PM, Engineer, Verifier) | 2 agents (Improver, Verifier) | PM role was overloaded; research and implementation should be one agent |
| Cost controls | "PM uses V2.5" (vague) | Per-agent token budgets with hard caps | Industry data: 68% of teams hit budget overruns in first deployments |
| Measurement | "feels better" | Baseline metrics + before/after comparison | "Done" must mean something verifiable |
| Memory | Flat file list | Structured: state vs knowledge vs objectives | Pattern from production agent systems |
| Stop conditions | "10 cycles" | Per-script quality thresholds | Prevents improvement churn |
| Research scope | "Find experts, read everything" | Scoped briefs with token budgets | Unscoped research burns tokens without value |
| Safety rails | 6 rails (generic) | 9 rails (concrete, enforceable) | Production failure modes identified by Anthropic, OpenAI |

## What Changed from v2 (Meta-Loop Findings)

| Area | v2 | v3 | Source |
|------|----|----|--------|
| Comprehension debt | Not addressed | Plain-English changelog per improvement | PM 1.1 (confirmed) |
| Existing patterns | Ignored | References subagent-driven-development, ward | PM 1.4 (confirmed) |
| Cron failure modes | Not addressed | Cron-specific safety rails added | PM 1.5 (confirmed) |
| Research context | Generic expert benchmark | Homelab-applicability filter | PM 2.1 (partial) |
| Verifier testing | "Run the script" | Formalized logic-test + live-test approach | PM 2.3 (confirmed) |
| Verifier model | V2.5 | Claude Sonnet via OpenRouter | PM 2.4 + 5.5 (confirmed) |
| Conversation dynamics | No guidance | "Challenge mode" instruction for Hermes | PM 3.1 (confirmed) |
| Post-commit monitoring | None | Rollback + monitoring after commit | PM 4.3 (confirmed) |
| Human feedback | None | Feedback mechanism for [USER] | PM 4.4 (confirmed) |
| Failed improvement tracking | Revert only | Abandon state after repeated failures | PM 5.6 (confirmed) |

## The Problem (unchanged)

We have 13 cron jobs frozen at the moment we wrote them. They don't learn from failures, don't adapt to infrastructure changes, and don't incorporate best practices we didn't know about when we wrote them.

## The Vision (unchanged)

Build a self-improving system where a meta-agent loop researches, improves, and verifies our existing scripts — approaching the quality of what a domain expert would produce.

## Architecture: Two-Agent Loop

### Why Two Agents, Not Three

**v1 had:** PM (research + vision) → Engineer (implementation) → Verifier (QA)

**Problem:** The PM role was doing too many things — identifying the craft, scouting experts, deep research, incident review, gap analysis, and prioritization. In practice, this means one agent with a massive prompt that burns tokens on each of these sub-tasks without clear boundaries. Anthropic's research on multi-agent systems found that agents with vague, overloaded instructions "duplicate work, leave gaps, or fail to find necessary information."

**v2 has:** Improver (research + implementation) → Verifier (adversarial QA)

**Why this works:**
- Research and implementation are naturally coupled — you can't implement well without understanding the domain, and research without implementation intent drifts
- The maker-checker split (the critical pattern) is preserved — the agent that writes code is never the agent that grades it
- Fewer coordination points = fewer failure modes
- Token spend is more predictable with 2 agents than 3

### Agent 1: Improver (Research + Implementation)

**Role:** For a given script, research what a domain expert would do differently, identify the highest-value improvement, and implement it.

**Process:**
1. **Read current state:** Load the script, its baseline metrics, and any previous cycle history
2. **Scoped research:** Using a pre-written research brief (see Research Briefs below), investigate what a master practitioner in this domain does differently. Token budget: 10K tokens max for research phase.
3. **Gap analysis:** Compare current script against research findings. Output: ranked list of concrete improvements with estimated impact.
4. **Implement top improvement:** One focused change. Write the modified script.
5. **Self-check:** Run the modified script locally. Does it execute? Does output match expected format?

**Output:** Modified script + change log explaining what was changed and why.

**Model:** Hermes with V2.5 Pro (coding quality matters here)

### Agent 2: Verifier (Adversarial QA)

**Role:** Test the modified script and confirm it actually improved. Different agent, different instructions from the Improver. Has hard veto power.

**Process:**
1. **Regression test:** Run the modified script against all relevant hosts. Does it still execute without errors?
2. **Output validation:** Does it produce valid output in the expected format?
3. **Improvement verification:** Does the improvement actually work? (Not just "it runs" but "it detects X that it missed before")
4. **Edge case testing:** What happens with no containers down? All containers down? Host unreachable? Empty output?
5. **Baseline comparison:** Compare output against the stored baseline. Are we detecting more, or the same, or (worse) less?

**Decision:**
- **PASS** → Commit the improvement, update baselines and cycle history
- **FAIL** → Revert to git snapshot, log failure reason, mark improvement as attempted-and-failed
- **PARTIAL** → Improvement works but has issues. Log specifics. Next cycle can address.

**Model:** Claude Sonnet via OpenRouter (different model, different training, different blind spots from V2.5 Pro — this is genuine model independence)

**Testing approach (formalized):**
The Verifier must confirm the improvement actually works, not just that the script runs. Use both:
1. **Logic tests:** Write a test script that exercises the new code's edge cases (positive cases, negative cases, boundary conditions). Run it. This works even when live hosts are unavailable.
2. **Live tests:** Run the script against actual hosts when possible. Compare output to baseline.
If only logic tests are possible (e.g., no containers are currently down), that's acceptable — but document which approach was used.

## Research Briefs (replacing "PM finds experts")

**Problem with v1:** "Find experts, read what they do" is unscoped. The agent could spend 50K tokens reading blog posts and still not have a concrete improvement to implement.

**v2 approach:** Pre-written research briefs per script domain. Each brief defines:
- What human role this script replaces
- 3-5 specific questions to research (not "everything about Docker")
- Where to look (specific sources, not "the internet")
- What constitutes a useful finding vs. noise
- Token budget for research phase

### Example Research Brief: ic-containers.py

```yaml
script: ic-containers.py
replaces: Senior Docker/SRE engineer
research_budget: 10000  # tokens

questions:
  - "What health checks do production Docker monitoring tools use beyond 'container running'?"
  - "What are the most common false positive patterns in container monitoring?"
  - "What auto-remediation actions are safe to take for container failures?"
  - "How do tools like cAdvisor, Prometheus container_exporter, and Datadog agent check container health?"

sources:
  - "Docker official documentation on container health checks"
  - "Prometheus container_exporter metrics"
  - "SRE books on monitoring best practices (Betsy Beyer et al.)"
  - "GitHub: popular docker monitoring projects (cAdvisor, docker-health-check)"

useful_finding: "A concrete check or metric we can add to the script"
noise: "General monitoring philosophy, tool comparisons without actionable specifics"
```

Research briefs are stored in `~/.hermes/data/loop-engineer/research-briefs/` and are written once per script domain, then reused across cycles. The Improver reads the brief, does focused research, and implements.

## Measurement Framework

### Baseline Metrics (captured before first cycle)

For each script, before any modification, run it and capture:

| Metric | How to Measure | What "Better" Means |
|--------|---------------|-------------------|
| **Detection count** | Number of issues/alerts detected | More = better (catching things we missed) |
| **False positive rate** | Alerts that don't correspond to real issues | Lower = better |
| **Execution time** | Wall-clock time to run | Should not increase significantly |
| **Output validity** | Does output parse correctly? | Must remain 100% |
| **Edge case handling** | Run with empty/unreachable inputs | More graceful = better |
| **Actionable output** | Does output include specific remediation steps? | More specific = better |

### Per-Cycle Measurement

After each cycle, the Verifier captures:
1. **Before snapshot:** Baseline metrics from the unmodified script
2. **After snapshot:** Metrics from the modified script
3. **Delta:** Explicit comparison (e.g., "Detection count: 5 → 8 (+3), False positives: 2 → 1 (-1)")
4. **Regression check:** Any metric that got worse?

### "Done" Criteria (when does a script stop needing improvement?)

A script is "done" when:
- [ ] It handles all failure modes identified in its research brief
- [ ] False positive rate is below 10% (or industry benchmark if available)
- [ ] It produces actionable output (not just "container X is down" but "container X is down, likely cause: Y, suggested action: Z")
- [ ] Two consecutive cycles produce no measurable improvement
- [ ] All edge cases from the research brief are handled gracefully

This prevents improvement churn — the loop stops when the script is genuinely good enough, not when we get bored.

## Token Budgets and Cost Controls

### Per-Agent Budgets

| Agent | Phase | Token Budget | Model |
|-------|-------|-------------|-------|
| Improver | Research | 10K tokens | V2.5 Pro |
| Improver | Implementation | 15K tokens | V2.5 Pro |
| Verifier | Testing + evaluation | 5K tokens | Claude Sonnet (OpenRouter) |
| **Total per cycle** | | **30K tokens** | |

### Budget Enforcement

1. **Hard cap:** If any agent exceeds its budget, the cycle is aborted. The Improver's partial work is saved as a draft for the next cycle.
2. **Research budget is separate from implementation:** Research can't eat into implementation tokens and vice versa.
3. **Verifier budget is small by design:** Testing a script should be fast. If the Verifier needs more than 5K tokens, the test design is wrong, not the script.

### Cost Tracking

Each cycle logs:
- Tokens used per agent per phase
- Total cost (estimated from model pricing)
- Cumulative cost per script
- Cost per improvement (total cost / number of improvements landed)

This lets [USER] see: "ic-containers.py has cost $X total, yielded Y improvements, average cost per improvement: $Z."

## Persistent State (restructured)

| File | Purpose | Written By | Type |
|------|---------|------------|------|
| `objectives.json` | **Read-only** top-level goals and constraints | [USER] (once) | Immutable |
| `script-state/<script>.json` | Current metrics, cycle count, last improvement, baseline | System | Mutable |
| `expert-knowledge/<domain>.md` | Accumulated domain knowledge from research | Improver | Append-only |
| `research-briefs/<script>.yaml` | Research scope and questions per script | [USER] + Hermes (once) | Static |
| `cycle-history.md` | What was tried, results, what worked, what failed | Improver + Verifier | Append-only |
| `script-baselines/` | Git snapshot of script before each modification | System | Immutable |

### Objectives Kernel (read-only)

```json
{
  "version": 1,
  "constraints": [
    "Scripts must run unattended without human intervention",
    "Scripts must complete within 5 minutes",
    "Alerts must be actionable (include what to do)",
    "No auto-remediation without explicit approval",
    "Output format must remain backward-compatible",
    "Total cycle cost must stay under $2 per cycle"
  ],
  "quality_targets": {
    "false_positive_rate": "< 10%",
    "edge_case_coverage": "all research brief cases handled",
    "detection_improvement": "> 20% over baseline"
  }
}
```

The Improver reads this at the start of every cycle. Any proposed change that violates a constraint is rejected before implementation.

## Safety Rails (concrete, enforceable)

| # | Rail | How It Works | Failure Mode It Prevents |
|---|------|-------------|------------------------|
| 1 | **Git commit before modification** | Auto-snapshot before any change | Instant rollback if something breaks |
| 2 | **Token budget per agent** | Hard cap, abort if exceeded | Runaway cost ($10K surprise bills) |
| 3 | **Verifier veto power** | Verifier can reject any change | Bad changes don't ship |
| 4 | **Objectives kernel** | Read-only constraints checked before implementation | Goal drift (agent optimizing wrong thing) |
| 5 | **Baseline comparison** | Before/after metrics required | "Improvement" that actually makes things worse |
| 6 | **Cycle history + failure tracking** | Failed improvements are logged with reasons | Repeated failures on same approach |
| 7 | **Two-agent model separation** | Improver and Verifier use different models | "Grading own homework" bias |
| 8 | **Research brief scoping** | Pre-defined questions and token limits | Unbounded research burning tokens |
| 9 | **Stop conditions** | Script declared "done" when quality thresholds met | Improvement churn (constant changes that don't add up) |
| 10 | **Comprehension debt tracking** | Every improvement gets a plain-English changelog (what, why, risk, undo) | [USER] loses understanding of his own scripts |
| 11 | **Cron failure detection** | Meta-loop monitors for silent cron failures; state files have checksums | Cron job fails silently, nobody notices |
| 12 | **Post-commit monitoring** | After commit, next 2 cycles check if improvement is still working | Improvement works in testing but fails over time |
| 13 | **Human feedback channel** | [USER] can flag bad improvements; objectives kernel updated | No mechanism for operator to reject changes |
| 14 | **Abandon state** | After 2 failures in same improvement direction, mark as abandoned | Repeatedly trying dead-end approaches |

## First Real Cycle: ic-containers.py

### Scope

**Script:** `~/.hermes/skills/incident-commander/scripts/ic-containers.py`
**Domain:** Container health monitoring (Docker)
**Research brief:** To be written (see template above)
**Baseline capture:** Run script, record current detection count, false positives, output format

### Cycle 1 Plan

1. **Capture baseline:** Run ic-containers.py, record metrics
2. **Improver phase:**
   - Read research brief for container monitoring
   - Research: What do production Docker monitoring tools check beyond "container running"?
   - Identify top improvement (likely: health check integration, restart count monitoring, or resource threshold alerts)
   - Implement one improvement
   - Self-check: does it run?
3. **Verifier phase:**
   - Run modified script against all hosts
   - Compare output to baseline
   - Check edge cases
   - PASS/FAIL decision
4. **If PASS:** Commit, update baselines, log to cycle-history.md
5. **If FAIL:** Revert, log failure, next cycle tries different approach

### Expected Timeline

- Baseline capture: 5 minutes
- Improver phase: 15-20 minutes (research + implementation)
- Verifier phase: 5-10 minutes
- **Total: ~30 minutes per cycle**

### Expected Cost

- ~30K tokens per cycle
- At V2.5 Pro pricing: ~$0.15-0.30 per cycle
- **10 cycles = ~$1.50-3.00 total** for ic-containers.py

## Open Questions (resolved from v1)

| v1 Question | v2 Answer |
|-------------|-----------|
| What's the right frequency? | Weekly, one script per week. 5 scripts × 2 cycles each = 10 weeks for first pass. |
| How do we measure "improvement" objectively? | Baseline metrics + before/after comparison (see Measurement Framework) |
| Should the PM incorporate incident data? | Yes, as one input to the research brief, not as the primary driver |
| How do we prevent improvement churn? | Stop conditions: two consecutive cycles with no measurable improvement = script is "done" |
| What's the right scope limit per cycle? | One improvement, 30K token budget, 30-minute wall clock |

## Comprehension Debt Tracking

Osmani's warning: "the gap that widens when a system ships code you never read." Every improvement committed by the loop MUST include a plain-English changelog:

- **What changed** (one sentence)
- **Why it changed** (the research finding that motivated it)
- **What could go wrong** (known risks)
- **How to undo it** (revert command or file to restore)

This is stored in `cycle-history.md` alongside each cycle's results. [USER] can read these to understand what his scripts do and why.

## Human Feedback Integration

[USER] can flag improvements as "bad" by editing `objectives.json` to add a constraint like:
```json
"no_docker_stats_monitoring": "[USER] rejected resource monitoring — too noisy for homelab"
```

The Improver reads objectives.json at the start of every cycle, so rejected approaches are permanently blocked.

## Post-Commit Monitoring

After an improvement is committed, the next 2 cycles include a check: "Is the previous improvement still working correctly?" If the check fails, the improvement is reverted and logged as a regression. This catches improvements that work in testing but fail over time.

## Abandon State for Improvements

If an improvement direction fails 2 consecutive times (e.g., "add resource monitoring" fails in Cycle N and Cycle N+1), it is marked as "abandoned" with an explanation. Future cycles skip abandoned directions. This prevents wasted cycles on dead ends.

## Existing Loop Patterns in Hermes

The Loop Engineer builds on patterns already present in Hermes:
- **subagent-driven-development**: Two-stage review (spec compliance + quality) with fix-and-retry
- **requesting-code-review**: Auto-fix loop (max 2 cycles)
- **ward**: Nightly governance audits
- **scribe**: Nightly session digests

The Loop Engineer is a specialization of these patterns — not a new concept. It adds research briefs, persistent state, and iterative improvement on top of the existing maker-checker foundation.

## Cron-Specific Failure Modes

Cron jobs have failure modes that interactive sessions don't:
- **Silent failures:** Job fails, nobody notices. Mitigation: meta-loop monitors for missing cycle entries.
- **Partial execution:** Job times out mid-cycle. Mitigation: state files are written atomically; incomplete cycles are logged as "aborted."
- **State corruption:** Multiple cycles write to same files. Mitigation: only one cycle runs at a time (cron schedule prevents overlap).
- **Resource contention:** Two cron jobs compete for CPU/memory. Mitigation: cycle time budget (30 min max).

## Homelab-Applicability Filter

Research briefs must include a homelab-applicability check. When evaluating expert practices, the Improver must ask:
- "Does this require infrastructure we don't have?" (e.g., Kubernetes, service mesh)
- "Is this designed for 10,000 containers or 20?"
- "Can this be implemented in a Python script with SSH access?"

Expert practices that require enterprise infrastructure are logged as knowledge but NOT implemented.

## Open Questions (new for v2)

1. **Research brief quality:** How do we know if a research brief is good enough? (Answer: try it, iterate on the brief if the Improver keeps finding noise)
2. **Verifier calibration:** How strict should the Verifier be initially? (Answer: start strict, relax if it rejects everything)
3. **Cross-script learning:** Should improvements to ic-containers.py inform ic-resources.py? (Answer: yes, via expert-knowledge/ shared directory)
4. **[USER] review cadence:** How often should [USER] review cycle results? (Answer: after every 3 cycles, or when a cycle fails twice on the same script)
