# Architecture Decisions — Loop Engineer (June 2026)

Key decisions made during the design session, with rationale.

## Decision: PM writes a brief BEFORE coding
**Context:** The Improver was doing 3 web searches then immediately coding. No documentation of research, no quality checkpoint.
**Decision:** PM must write a structured improvement brief to `current-brief.md` before any implementation.
**Rationale:** The brief is the handoff document. It catches weak research before code is written. [USER]: "That exactly what the pm should do is hand off what it's researched and learned."

## Decision: Verifier checks research quality, not just code
**Context:** Verifier only checked if the code worked. Bad research could produce correct code that wasn't the right improvement.
**Decision:** Verifier rates research STRONG/ADEQUATE/WEAK and checks if the recommendation was the highest-impact option.
**Rationale:** The Verifier is the quality gate for the entire pipeline, not just the implementation.

## Decision: Bad research feeds back into the backlog
**Context:** When the Verifier rejected work, it just reverted. Next cycle could make the same mistake.
**Decision:** Verifier runs `loop-engineer-feedback.py --verifier "..."` to log specific failures in the backlog.
**Rationale:** Continuous improvement requires learning from failures. The backlog is the memory of what went wrong.

## Decision: Self-improvement is job #14
**Context:** The Loop Engineer system itself was not in the improvement rotation. [USER]: "Are the cron jobs selected based on a backlog?"
**Decision:** Job #14 is the Loop Engineer itself. Every 4th cycle, improve the process.
**Rationale:** A system that can't improve itself isn't truly continuous improvement.

## Decision: Dynamic backlog from feedback, not static list
**Context:** The improvement backlog was manually written and never updated.
**Decision:** Backlog is populated by feedback ingestion script, incidents, verifier findings, and system self-assessment.
**Rationale:** Real problems should drive improvement, not just web research about best practices.

## Decision: Strip back before building up
**Context:** System expanded from "improve scripts" to "AgentOps SDLC with advisory board" in 115 minutes before running a single cycle.
**Decision:** Prove the basic Improve→Verify loop works before adding governance layers.
**Rationale:** [USER]: "Ok go ahead and strip and test the basics then we'll build back up." Complexity before validation is scope creep.

## Decision: Two models for independence
**Context:** Same model grading its own work is "grading your own homework."
**Decision:** Improver on V2.5 Pro, Verifier on Claude Sonnet via OpenRouter.
**Rationale:** Anthropic's data shows cross-model verification is the single most important structural move for agent quality.

## Decision: User is not the domain expert
**Context:** [USER]: "I don't know what I don't know. I'm hiring this team."
**Decision:** The PM must identify architectural gaps without user direction. If it only finds technical improvements, it's a junior PM.
**Rationale:** The system should be smarter than the humans who built it.
