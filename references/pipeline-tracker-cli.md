# Pipeline Tracker CLI Reference

Exact command syntax for `~/.loopforge/scripts/pipeline-tracker.py`.

## record-cost

Records estimated vs actual cost for a proposal.

```bash
python3 ~/.loopforge/scripts/pipeline-tracker.py record-cost \
  --id prop-001 \
  --estimated 0.25 \
  --actual 0.25
```

- `--id`: Proposal ID (e.g., `prop-001`)
- `--estimated`: Float, the original cost estimate from the proposal
- `--actual`: Float, the real cost from the Code Writer's output

## record-outcome

Records claimed vs measured value (for outcome tracking over time).

```bash
python3 ~/.loopforge/scripts/pipeline-tracker.py record-outcome \
  --id prop-001 \
  --claimed 0.50 \
  --measured 0.0 \
  --notes "Preventive improvement — measured value requires accumulation over time"
```

**⚠️ Args must be plain floats**, not strings like `"0.50/week"`. Error: `invalid float value`.

- `--id`: Proposal ID
- `--claimed`: Float — the `value_per_week` from the proposal
- `--measured`: Float — actual measured impact. Use `0.0` for preventive improvements on first cycle.
- `--notes`: String (optional) — context for the measurement
- `--verified`: Flag (optional) — mark as externally verified

### Preventive Improvements

When the claimed value is "prevents X incidents/year," set `--measured 0.0` on first cycle. The outcome report will show "Inaccurate" — this is expected. After enough cycles to observe incident rates, update with real measurement.

## add-feedback

Records committee feedback for the PM to learn from.

```bash
python3 ~/.loopforge/scripts/pipeline-tracker.py add-feedback \
  --id prop-001 \
  --member priority_arbitrator \
  --vote DEFER \
  --reason "Low impact"
```

## Reports

```bash
python3 ~/.loopforge/scripts/pipeline-tracker.py cost-report        # Estimate vs actual
python3 ~/.loopforge/scripts/pipeline-tracker.py outcome-report     # Claimed vs measured
python3 ~/.loopforge/scripts/pipeline-tracker.py feedback-for-pm    # Committee feedback
python3 ~/.loopforge/scripts/pipeline-tracker.py pm-context         # Generate PM context JSON
```

## pm-context

Generates `~/.loopforge/data/loop-engineer/pm-context.json` — the PM reads this at the start of each cycle.

The generated file is minimal (cost learning + outcome learning). The Engineering Phase should enrich it manually with:
- `known_issues` — pipeline bugs (e.g., "Budget Analyst parse failures")
- `backlog_for_next_cycle` — deferred/escalated items summary
- `cycle_summary` — high-level stats for the cycle just completed
