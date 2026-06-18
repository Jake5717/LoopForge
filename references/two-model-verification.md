# Two-Model Verification Pattern

## Why Different Models Matter

Anthropic's internal data shows that cross-model verification is the single most important structural move for agent quality. A model grading its own output is too generous — same training data, same tendencies, same blind spots. Different models have different failure modes, so a second model catches what the first one reasoned itself into.

## Implementation via Cron

Two sequential cron jobs with `context_from`:

| Job | Cron | Model | Role |
|-----|------|-------|------|
| Improver | `0 10 * * 0` | V2.5 Pro (Xiaomi) | Research + implement |
| Verifier | `30 10 * * 0` | Claude Sonnet (OpenRouter) | Adversarial review |

The Verifier job uses `context_from=[improver_job_id]` — this injects the Improver's most recent completed output as context. The 30-minute gap ensures the Improver has finished.

## Why Claude Sonnet Specifically

- Different training data than V2.5 Pro
- Different tendencies (more cautious, more analytical)
- Different blind spots (catches errors V2.5 Pro would miss)
- Genuine independence — not just "same model with different instructions"

## Cost Impact

- V2.5 Pro: ~$0.02 per improvement cycle
- Claude Sonnet via OpenRouter: ~$0.09 per verification
- Total: ~$0.11 per full cycle

The Verifier is the most expensive single component but provides the highest quality assurance value.

## Key Insight

Same-model verification is "grading your own homework." Cross-model verification is hiring an external auditor. The cost difference is small; the quality difference is large.
