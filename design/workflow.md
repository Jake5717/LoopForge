# Loop Engineer — Workflow Description

Open the diagram: `loop-engineer-workflow.excalidraw` at [excalidraw.com](https://excalidraw.com) (drag and drop the file).

## Step-by-Step

### 1. INPUT SOURCES (top row)

Four ways problems enter the system:

| Source | What It Is | Example |
|--------|-----------|---------|
| **[USER]'s Feedback** | You tell me something's wrong | "container-monitor.py gave a wrong alert" |
| **Incidents** | Something actually broke | Container crash, disk full, service down |
| **Verifier Findings** | Previous cycle found a gap | "error-scanner.py missing cross-host correlation" |
| **System Gaps** | The system identifies its own weakness | "Advisory Board from cron doesn't work" |

**How feedback gets ingested:** I run `python3 ~/.loopforge/scripts/loop-engineer-feedback.py --feedback "..."` and it adds the item to `backlog.md` under the relevant job.

### 2. DYNAMIC BACKLOG

`backlog.md` — a prioritized list of everything that needs improvement. Items are sorted by:
- **Urgency** — incidents and [USER]'s feedback come first
- **Recency** — jobs not improved recently get priority
- **Impact** — high-value improvements ranked above nice-to-haves

The backlog is **not static**. It's fed by the four input sources above. Every cycle, the Improver reads it and picks the highest-priority item.

### 3. IMPROVER (V2.5 Pro)

Runs Sunday at 10:00 AM. This agent does three things:

**a) Pick a job:** Reads the backlog, picks the most urgent/improvable job from the full inventory of 14 jobs (13 cron jobs + the Loop Engineer itself).

**b) Research:** Searches the web for "what would a $180K/year expert in this domain do differently?" Reads 3-5 high-quality sources. Stays within a 10K token research budget.

**c) Implement:** Makes ONE focused change to the chosen job. Could be:
- A Python script improvement (for script-based jobs)
- A prompt improvement (for agent-based jobs)
- A process improvement (for the Loop Engineer itself)

**Rules:** One improvement per cycle. Preserve existing behavior. Add comments explaining changes.

### 4. VERIFIER (Claude Sonnet)

Runs Sunday at 10:30 AM — 30 minutes after the Improver. **Different model, different training, different blind spots.**

The Verifier is **adversarial by design:**
- "The Improver is not your friend"
- "Find every flaw"
- "It runs" isn't enough — must be measurably better

**Checks:**
- Syntax (does it execute?)
- Edge cases (host unreachable, all down, normal operation)
- Regressions (did it break existing behavior?)
- Value (is the improvement actually useful?)

**Verdict:** PASS or FAIL with specific evidence.

### 5. DECISION DIAMOND (PASS / FAIL)

| Result | What Happens |
|--------|-------------|
| **PASS** | Improvement proceeds to Steering Summary |
| **FAIL** | Script reverts to baseline. Failure logged in cycle-history.md. Next cycle tries a different approach. |

### 6. STEERING SUMMARY

A plain-English summary delivered to [USER]:

```
Job: container-monitor.py
What: Added healthcheck detail reporting
Verdict: PASS
Cost: ~$0.53
Your call: "ship it" / "skip" / "reprioritize"
```

[USER] doesn't need to evaluate container monitoring best practices. He reads one paragraph and decides.

### 7. [USER] DECIDES

| Response | What Happens |
|----------|-------------|
| **"ship it"** | Engineering Phase commits the change |
| **"skip"** | Improvement is discarded, logged as skipped |
| **"reprioritize"** | [USER] tells the system what to work on instead |

### 8. ENGINEERING PHASE

If [USER] says "ship it":
- Change is committed (or snapshotted if not in git)
- `changelog.md` updated with what/why/risk/undo
- `cycle-history.md` updated with results
- `expert-directory.json` updated with new sources
- `backlog.md` updated (completed item removed, new items added)

### 9. STATE FILES (bottom)

All state persists across cycles:

| File | What It Tracks |
|------|---------------|
| `backlog.md` | What needs improving (dynamic, fed by feedback) |
| `cycle-history.md` | What was tried, what worked, what failed |
| `changelog.md` | Every change committed, with undo instructions |
| `expert-directory.json` | Domain experts discovered during research |
| `script-baselines/` | Snapshots before modification (for rollback) |

### 10. THE LOOP

After the Engineering Phase, the cycle is complete. Next Sunday, the Improver reads the updated backlog (which now includes any new feedback or issues discovered), and the loop starts again.

**Self-improvement:** Every 4th cycle, the Improver picks Job #14 (the Loop Engineer itself) and improves the process — better selection logic, clearer prompts, faster feedback ingestion.

## Timing

| Time | What Runs |
|------|-----------|
| Sunday 10:00 AM | Improver (V2.5 Pro) — research + implement |
| Sunday 10:30 AM | Verifier (Claude Sonnet) — adversarial review |
| Sunday ~11:00 AM | Summary delivered to [USER] |
| Anytime | [USER] gives feedback → ingested into backlog |
| Every 4th Sunday | Self-improvement cycle |

## Cost

~$0.40-0.60 per weekly cycle. ~$20-30 per year.
