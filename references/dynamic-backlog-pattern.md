# Dynamic Backlog Pattern

## Overview

The Loop Engineer's backlog is NOT a static list — it's fed by real problems from four sources. This is the "continuous" in continuous improvement.

## Backlog Location

`~/.loopforge/data/loop-engineer/backlog.md`

## How Items Get Added

### 1. [USER]'s Feedback (highest priority)
When [USER] says "that script was wrong" or "container-monitor gave a bad alert":
```bash
python3 ~/.loopforge/scripts/loop-engineer-feedback.py --feedback "container-monitor.py false positive on NAS/host containers"
```

### 2. Incidents
When `~/.loopforge/incidents/` gets a new file, the relevant job gets prioritized:
```bash
python3 ~/.loopforge/scripts/loop-engineer-feedback.py --incident ~/.loopforge/incidents/<DATE>-<incident-name>.md
```

### 3. Verifier Findings
When the Verifier flags something in a previous cycle:
```bash
python3 ~/.loopforge/scripts/loop-engineer-feedback.py --verifier "error-scanner.py missing cross-host correlation"
```

### 4. System Self-Assessment
When the Loop Engineer identifies its own process gaps:
```bash
python3 ~/.loopforge/scripts/loop-engineer-feedback.py --system "Selection logic keeps picking container-monitor — needs broader rotation"
```

## Backlog Format

```markdown
### [Job Name]
- [ ] [Issue description] — [source: [USER]/incident/verifier/system] — [date]
```

## Selection Logic (Priority Order)

1. **Backlog items with highest urgency** — incidents and [USER]'s feedback first
2. **Jobs not improved recently** — check cycle-history.md
3. **Self-improvement** — every 4th cycle, pick job #14
4. **Generic improvements** — only if no backlog items exist

## Key Principle

Real problems first, nice-to-haves second. The backlog should shrink over time as the system improves. If the backlog is empty, the system is working well — pick the job with the longest time since improvement.

## Pilot Findings (2026-06-12)

The initial backlog was static (manually written). [USER] corrected this: "Are cron jobs selected based on a backlog of issues that are discovered or brought up by me?" — the answer should be YES, and the feedback ingestion process was created to make it so.

Job #14 (self-improvement) was also missing from the original inventory. [USER]: "Does this cron job also go through the self improvement loop?" — added as a requirement.
