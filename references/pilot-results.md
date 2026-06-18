# Loop Engineer — Pilot Results

## Pilot 1: ic-containers.py (Manual, 2026-06-12)

**Improvement:** Added `get_healthcheck_details()` — queries `docker inspect` for failing streak, exit code, and output when container is unhealthy.

**Improver (V2.5 Pro):** 1,023,946 input / 4,349 output tokens | $0.45 | 184 seconds
**Verifier (V2.5 Pro):** 190,254 input / 2,569 output tokens | $0.09 | 82 seconds
**Total:** 1,214,200 input / 6,918 output | **$0.53** | 4.5 minutes

**Result:** PASS — "converts a binary 'unhealthy' signal into actionable diagnostic data"

**Key finding:** Token costs were 5x higher than estimates because subagents read full scripts (500+ lines) and do web searches with cumulative context.

## Pilot 2: Cron-based (Failed, 2026-06-12)

**What failed:**
1. `delegate_task` from cron never spawned the 4 Advisory Board subagents
2. `context_from` chaining delivered zero context to the Verifier
3. Token costs 14x over budget ($1.50 vs $0.11) due to retry loops

**Root cause:** Assumed `delegate_task` and `context_from` work from cron without testing first.

**Resolution:** Stripped to 2-agent basic loop, validated manual pilot, then built 4-step pipeline with verified infrastructure.

## Lessons

1. Test infrastructure before building on it
2. Run manual pilot before automated deployment
3. Budget 3-5x estimates for real-world token usage
4. `delegate_task` from cron is untested — use `claude -p` via terminal instead
5. `context_from` may be unreliable — verify context injection works
