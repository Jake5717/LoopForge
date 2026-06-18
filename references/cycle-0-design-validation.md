# Cycle 0 Design Validation Findings

**Date:** 2026-06-12
**Result:** PASS — v1 revised to v2

## Research Sources

PM researched 20+ articles on loop engineering, self-improving agents, and multi-agent production systems. Key sources:

- Addy Osmani's loop engineering post (June 2026) — coined the term
- Boris Cherny (Anthropic, Claude Code) — "I write loops, not prompts"
- Anthropic's multi-agent research data (token costs, role overload)
- HashiCorp Mitchell Hashimoto's agent patterns
- Various production multi-agent system reports

## Gaps Found in v1

| Gap | Severity | v1 Had It? | v2 Fix |
|-----|----------|-----------|--------|
| No token budgets → could burn $10K+ | HIGH | No | 30K hard cap per cycle |
| PM role overloaded → wasted tokens, poor research | HIGH | Yes (6 responsibilities) | Merged PM + Engineer = Improver |
| No measurement framework → "improvement" undefined | HIGH | No | 6 baseline metrics with definitions |
| No stop conditions → improvement churn | MEDIUM | No | Two consecutive non-improvement cycles = done |
| Flat memory → no state vs knowledge separation | MEDIUM | Partial | Structured state files (objectives, state, knowledge) |
| Research scope unbounded → reads everything, implements nothing | MEDIUM | Yes | Research briefs with scoped questions + token limits |
| No goal alignment mechanism → drift over time | MEDIUM | No | Objectives kernel (read-only constraints) |

## Key Statistics (from Anthropic data)

- Multi-agent systems burn **15x more tokens** than single-agent chats
- **68% of teams** hit budget overruns in first multi-agent deployments
- Overloaded agents "duplicate work, leave gaps, or fail to find information"

## Design Changes: v1 → v2

1. **3 agents → 2 agents** — PM and Engineer merged into "Improver"
2. **Token budgets added** — 10K research + 15K implementation + 5K verification = ~$0.15-0.30/cycle
3. **Measurement framework** — 6 metrics with explicit "better" definitions
4. **Stop conditions** — false positive rate <10% + two consecutive non-improvement cycles
5. **Research briefs** — pre-scoped plans per script (5 questions, defined sources)
6. **Objectives kernel** — read-only constraints checked before implementation
7. **Structured state** — objectives (immutable), state (mutable), knowledge (append-only)

## Verification Criteria (all passed)

- [x] Agent roles clearly defined (2 agents, no overlap)
- [x] Explicit input/output formats for each role
- [x] 9 safety rails address identified failure modes
- [x] Concrete cost controls (token budgets with hard caps)
- [x] Objective measurement criteria (6 metrics with definitions)
- [x] Clear termination conditions (quality thresholds + consecutive non-improvement)
- [x] Practical incident integration (input to research brief)
- [x] First real cycle clearly scoped (container-monitor.py)
