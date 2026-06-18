# Loop Engineer — Design Document v1

**Date:** 2026-06-12
**Status:** Draft — pending PM validation
**Authors:** [USER] + Hermes

## The Problem

We have 13 cron jobs doing monitoring, security, governance, and content tasks. They're frozen at the moment we wrote them. They don't learn from failures, don't adapt to infrastructure changes, and don't incorporate best practices we didn't know about when we wrote them. [USER] and I don't know what we don't know — our scripts are limited by our own knowledge.

## The Vision

Build a self-improving system where a meta-agent loop researches, improves, and verifies our existing scripts — approaching the quality of what a domain expert would produce, without requiring [USER] or me to become domain experts.

## Architecture: Three-Agent Loop

### Agent 1: Product Manager (Research + Vision)

**Role:** Identifies the human craft that each script replaces, researches what a master practitioner in that craft actually does, and defines the gap between what we have and what "awesome" looks like.

**Process:**
1. **Identify the craft:** What human role does this script replace? (e.g., `ic-containers.py` replaces a senior Docker/SRE engineer)
2. **Scout for experts:** Search for who the recognized experts are in that domain. Check the expert directory (persistent state). Find new voices.
3. **Deep research:** Read what experts actually do — blog posts, conference talks, books, open-source projects. Focus on: best practices, failure modes, optimization techniques, professional workflows.
4. **Incident feedback:** Review recent incidents and script failures — what did we miss? What should we have caught?
5. **Gap analysis:** "Here's what we have vs what a master practitioner would do."
6. **Output:** Prioritized improvement brief for the Engineer.

**Key distinction:** The PM doesn't just search "docker health check scripts." It asks "what would a $180K/year senior SRE know and do that our script doesn't?"

### Agent 2: Loop Engineer (Implementation)

**Role:** Translates the PM's improvement brief into working code changes. One improvement per cycle.

**Process:**
1. Read the improvement brief from the PM
2. Implement the top-priority improvement
3. One focused change per cycle — no massive rewrites
4. Ensure backward compatibility (output format, behavior)
5. Write the modified script

### Agent 3: Verifier (Quality Assurance)

**Role:** Tests the modified script and confirms it actually improved. Different agent, different instructions from the Engineer.

**Process:**
1. Run the modified script against all relevant hosts
2. Check: does it still execute without errors?
3. Check: does it produce valid output in the expected format?
4. Check: does the improvement actually work? (Not just "it runs" but "it's better")
5. Check: edge cases — what happens with no containers down? All containers down? Host unreachable?
6. **PASS** → Commit the improvement
7. **FAIL** → Revert, explain what broke

## Persistent State

| File | Purpose | Written By |
|------|---------|------------|
| `expert-directory.json` | Curated list of domain experts + sources per domain | PM |
| `improvement-backlog.md` | Prioritized gaps between current script and expert-level | PM |
| `cycle-history.md` | What was tried, results, what worked, what failed | Engineer + Verifier |
| `script-baselines/` | Git snapshot of script before each modification | System |

## Cron Jobs to Improve (Priority Order)

| Script | Human Role | Priority | Why |
|--------|-----------|----------|-----|
| `ic-containers.py` | Senior Docker/SRE engineer | 1 | Highest impact — monitors all containers |
| `ic-resources.py` | Capacity planning engineer | 2 | Predicts disk/memory issues |
| `ic-errors.py` | Observability engineer | 3 | Log analysis and error detection |
| `network-guard.py` | Network security analyst | 4 | Security monitoring accuracy |
| `network-guard.py --analyze` | Threat intelligence analyst | 5 | Anomaly detection quality |

## Safety Rails

1. **Git commit before modification** — instant rollback if something breaks
2. **One change per cycle** — no blast radius
3. **Verifier must pass** — nothing goes live without quality gate
4. **Cycle history tracking** — prevents repeated failures
5. **PM research is logged** — [USER] can see what it found and why
6. **Human approval for Tier 3 changes** — massive rewrites need [USER]'s sign-off

## Cost Considerations

- PM research is token-heavy (web searches + synthesis)
- Engineer implementation is moderate (code editing)
- Verifier is lightweight (running script + checking output)
- **Mitigation:** PM runs weekly, Engineer + Verifier run after PM completes
- **Mitigation:** PM uses V2.5 for research, Engineer uses V2.5 Pro for coding

## Open Questions (for PM to investigate)

1. What's the right frequency? Weekly? Biweekly? Per-script cadence?
2. How do we measure "improvement" objectively, not just "it still works"?
3. Should the PM incorporate real incident data from `~/.loopforge/incidents/`?
4. How do we prevent improvement churn (constant small changes that don't add up)?
5. What's the right scope limit per cycle?

## Success Criteria

After 10 cycles (10 weeks), we should see:
- `ic-containers.py` handles 3+ failure modes it doesn't today
- False positive rate decreased (fewer unnecessary alerts)
- At least one auto-remediation that works correctly
- Expert directory has 10+ curated sources across all domains
- Cycle history shows consistent improvement trajectory
