# Cost Model

## Overview

LoopForge operates on a weekly budget. The system is designed to maximize improvement per dollar while preventing runaway costs.

## Weekly Budget

- **Default**: $3/week (configurable)
- **Typical spend**: $1.50–2.50 per cycle
- **Annual cost**: ~$80–130

## Cost Breakdown Per Cycle

| Step | Model Type | ~Cost | % of Budget |
|------|-----------|-------|-------------|
| PM Research | Research-optimized (cheap) | $0.25 | 8% |
| Idea Verifier | Fast/cheap (e.g., Gemini Flash) | $0.05 | 2% |
| Steering Committee | 3 cheap models (parallel) | $0.15 | 5% |
| Code Writer | Coding model (e.g., Claude Code) | $0.60 | 20% |
| Code Verifier | Different family (e.g., GPT-4o) | $0.25 | 8% |
| **Subtotal (pipeline)** | | **$1.30** | **43%** |
| Auto-shipped improvements | | $0.20–1.20 | 7–40% |
| **Total** | | **$1.50–2.50** | **50–83%** |

The pipeline itself costs ~$1.30. The rest of the budget goes to implementing the improvements.

## ROI Analysis

Each proposal includes a `value_per_week` estimate. The committee uses this for ROI analysis:

- **ROI** = value_per_week / cost_estimate
- **Payback period** = cost_estimate / value_per_week (weeks to break even)

Example:
- Proposal: "Add health check endpoint to container monitor"
- Cost estimate: $0.40
- Value estimate: "Saves ~10 min/week in manual checks"
- ROI: 2.5x (if 10 min = $0.50/week labor value)
- Payback: 0.8 weeks

## Cost Tracking

After the Code Writer implements, it records actual cost vs estimate:

```
Estimated: $0.40
Actual: $0.45
Delta: +$0.05 (+12.5%)
```

Over time, the tracker learns: "The PM consistently underestimates by ~15%." This feeds back to the PM for better estimation.

## Budget Exhaustion

If the weekly budget runs out mid-cycle:
1. Already-implemented items are committed normally
2. Remaining proposals defer to next sprint
3. Deferred items are logged with "budget exhausted" reason
4. Next sprint's PM sees the backlog and can reprioritize

## Cost Optimization Strategies

### Model Selection
- Use the cheapest model that can do the job
- Fast/cheap models (Gemini Flash) for binary pass/fail decisions
- Expensive models only where reasoning quality matters

### Token Efficiency
- Keep prompts concise — longer prompts = more tokens = more cost
- MiMo models truncate at ~1200 tokens — keep prompts short for those
- Use structured output (JSON) to minimize response tokens

### Batch Processing
- Evaluate 3–5 proposals per cycle (not just 1)
- Amortize the fixed cost of each pipeline step across multiple proposals

## Real-World Cost Incident

See [Idea Verifier Cost Incident](../references/idea-verifier-cost-incident.md) for a real case where using the wrong model (Claude Sonnet instead of Gemini Flash) for the Idea Verifier burned ~$5 in 2 days. The fix: swap to a cheaper model for binary pass/fail decisions. Cost dropped from ~$0.80/run to ~$0.05/run.
