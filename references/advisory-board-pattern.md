# Advisory Board Pattern

## Purpose

Four independent expert agents debate a recommendation before it reaches the human decision-maker. Each expert has different instructions, different evaluation criteria, and different domain knowledge. The human gets a summary of expert consensus, not raw technical details.

## When to Use

- Any decision that requires domain expertise the human doesn't have
- Before committing to a technical improvement with real risk
- When the Improver proposes something that could affect production systems
- When prioritizing between multiple possible improvements

## The Four Expert Roles

### 1. SRE / Domain Expert
- **Question:** "Is this a real best practice that senior engineers actually use?"
- **Evaluates:** Technical merit, industry standards, whether this solves a real problem
- **Verdict:** HIGH_VALUE / MEDIUM_VALUE / LOW_VALUE / WRONG_APPROACH

### 2. Cost Analyst
- **Question:** "Is it worth the tokens?"
- **Evaluates:** Token cost, operational cost, ROI, cheaper alternatives
- **Verdict:** COST_EFFECTIVE / MARGINAL / TOO_EXPENSIVE

### 3. Risk Assessor
- **Question:** "Could this break things?"
- **Evaluates:** Blast radius, false positive risk, rollback path, critical code paths
- **Verdict:** LOW_RISK / MEDIUM_RISK / HIGH_RISK

### 4. Prioritization Expert
- **Question:** "Should we do this first?"
- **Evaluates:** Impact vs effort, alignment with frequent failures, backlog ordering
- **Verdict:** RIGHT_PRIORITY / SHOULD_WAIT / WRONG_PRIORITY

## Implementation (via delegate_task)

Each expert is spawned as an independent subagent:
```python
delegate_task(
    goal="You are a [ROLE]. Evaluate this improvement from your domain perspective.",
    context="[describe improvement, relevant context, what to evaluate]",
    toolsets=["terminal", "file"]
)
```

**Independence:** Experts do NOT see each other's evaluations. Each runs in isolation.

**Same model acceptable:** The experts can all run on the same model (V2.5 Pro). Independence comes from the instructions, not necessarily different models. The critical model split is between Improver and Verifier, not between experts.

## Synthesis

After all 4 experts respond, compile:
- Each expert's verdict and justification
- Expert consensus (how many agree?)
- Any conditions or concerns raised
- Recommended next step for the human

## Key Insight (from [USER])

The human said: "I don't know what I don't know. My creativity is limited." The Advisory Board solves this — it's a panel of experts that debate recommendations, so the human doesn't need to evaluate technical details themselves. They just read the consensus and decide "agree" or "override."
