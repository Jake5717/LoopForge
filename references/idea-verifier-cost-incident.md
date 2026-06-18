# Idea Verifier Cost Incident (2026-06-14)

## What Happened

[USER] reported ~$5 in OpenRouter charges over June 12-14. Root cause: Claude Sonnet 4 through OpenRouter was used for the Idea Verifier step, which made many API calls with large contexts.

## Timeline

### June 12, ~9:37 PM
Two "Meta" Loop Engineer jobs ran simultaneously using Sonnet:
- `Loop Engineer — Meta: Full Conversation Review (Verifier)` (<CRON_JOB_ID>)
- `Loop Engineer — FULL PILOT Verifier (Claude Sonnet)` (<CRON_JOB_ID>)

These were test/pilot jobs that no longer exist in the cron list but left charges behind.
Total: ~39 Sonnet API calls, 60K-117K input tokens each (~4M total).

### June 14, 10:15 AM
The regular Idea Verifier (Step 2) ran with Sonnet:
- 16 API calls in one session
- 65K-92K input tokens per call (~1.2M total)
- Multiple tool-call rounds re-reading the full proposals context each time

### Total Exposure
~55 Sonnet API calls through OpenRouter at ~$3-15/Mtok input = ~$4-5 total.

## Root Causes

1. **Sonnet is expensive per-token** — $3/Mtok input through OpenRouter
2. **Multi-turn tool calls multiply cost** — each round sends full context (70-90K tokens)
3. **Stale jobs** — deleted jobs from Jun 12 still had charges
4. **No cost monitoring** — no alert when a job exceeds expected cost

## Fix

Swapped Idea Verifier cron job (<CRON_JOB_ID>) from `anthropic/claude-sonnet-4` to `google/gemini-2.5-flash`.

**Why Gemini Flash is sufficient:** The Idea Verifier's job is gap analysis and research quality checks — it reads proposals and evaluates whether the PM's research is solid and the gaps are accurate. This doesn't require Sonnet-level reasoning. Gemini Flash handles structured analysis well at a fraction of the cost.

**Cost comparison:**
- Sonnet: ~$0.80/run (16 calls × 80K tokens × $3/Mtok)
- Gemini Flash: ~$0.05/run (same volume at ~$0.075/Mtok)

## Prevention

- Monitor OpenRouter credits weekly
- Check cron job models periodically for expensive outliers
- Consider adding cost alerts per-job if OpenRouter supports them
