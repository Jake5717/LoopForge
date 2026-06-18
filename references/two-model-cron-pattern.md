# Two-Model Cron Verification Pattern

A general-purpose pattern for running adversarial verification across different AI models using sequential cron jobs.

## Problem

A single agent grading its own output is too generous. Anthropic's data shows this is the #1 quality issue in agent systems. Same-model verification provides false confidence.

## Solution

Two sequential cron jobs on different models, connected via `context_from`:

### Job 1: Worker (V2.5 Pro)

```yaml
name: "Worker Job"
model:
  provider: xiaomi
  model: mimo-v2.5-pro
schedule: "0 10 * * 0"
```

Does the actual work (coding, research, implementation).

### Job 2: Reviewer (Claude Sonnet via OpenRouter)

```yaml
name: "Reviewer Job"
model:
  provider: openrouter
  model: anthropic/claude-sonnet-4
context_from: ["worker_job_id"]
schedule: "30 10 * * 0"  # 30 min after worker
```

Reviews the worker's output adversarially. Runs on a different model for genuine independence.

## Why This Works

- **Different training data** → different blind spots
- **Different tendencies** → one model's blind spot is caught by the other
- **No shared context** → the Verifier only sees the output, not the reasoning
- **Explicit adversarial instructions** → "find every flaw", "it runs is not enough"

## Implementation Notes

- `context_from` injects the most recent COMPLETED output — schedule the reviewer 30+ min after the worker
- If the worker fails, the reviewer still runs (it reviews the failure, not the success)
- The reviewer can REVERT changes — it has veto power
- Log both worker output and reviewer verdict in a shared state file

## Use Cases Beyond Loop Engineering

- Code review (worker writes code, reviewer on different model checks it)
- Document drafting (worker writes, reviewer checks accuracy/tone)
- Research synthesis (worker researches, reviewer validates claims)
- Any task where self-review provides false confidence

## Cost

- V2.5 Pro (worker): ~$0.05-0.15 per run
- Claude Sonnet (reviewer): ~$0.02-0.05 per run
- Total: ~$0.07-0.20 per cycle
- 10 cycles/month = ~$0.70-2.00/month

## Key Rule

The reviewer MUST be on a different model than the worker. Same-model verification is not verification — it's confirmation bias.
