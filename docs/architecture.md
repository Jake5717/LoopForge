# Architecture

## Overview

LoopForge is a 6-step pipeline that runs weekly. Each step is isolated — different models, different providers, different prompts. The system improves all automation scripts and cron jobs on a rotating basis.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  1. PM      │────▶│ 2. Idea      │────▶│ 3. Steering     │
│  Research   │     │    Verifier  │     │    Committee    │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                              ┌─────────────────────┤
                              │ Auto-ship    Escalate to human
                              ▼                     │
                    ┌─────────────────┐             │
                    │ 4. Code Writer  │◀────────────┘
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ 5. Code Verifier│
                    └────────┬────────┘
                             │ PASS
                             ▼
                    ┌─────────────────┐
                    │ 6. Engineering  │
                    │    Phase        │
                    └─────────────────┘
```

## Core Principles

### 1. No Model Grades Its Own Homework

Every step uses a different AI model from a different company. The PM researches with one model. The Idea Verifier critiques with another. The Code Writer implements with a third. The Code Verifier reviews with a fourth.

This prevents confirmation bias — the same blind spots that let a model write weak code will also let it approve weak code.

### 2. Research Before Code

The PM does real research before any proposals are written:
- Reads the current script/job to understand what it does today
- Checks the backlog for specific reported issues
- Searches for expert sources: GitHub repos, official docs, practitioner forums
- Reads 3-5 sources in depth
- Synthesizes: "What does a master practitioner do that we don't?"

### 3. Governance Through Debate

The Steering Committee isn't a rubber stamp. Three independent models argue about each proposal:
- **Budget Analyst**: "Is this worth the cost? Is the value estimate real?"
- **Risk Assessor**: "What could go wrong? Blast radius? Security?"
- **Priority Arbitrator**: "Is this the best use of our budget this sprint?"

They evaluate independently before comparing notes — no groupthink.

### 4. Budget-Limited Autonomy

The system operates within a weekly budget. Small fixes auto-ship. Medium and major changes require human approval. This creates genuine autonomy within guardrails.

## Model Selection

| Step | Recommended Model Type | Why |
|------|----------------------|-----|
| PM | Research-optimized (cheap, good at synthesis) | Needs to read many sources and synthesize findings |
| Idea Verifier | Fast, cheap model (e.g., Gemini Flash) | Binary pass/fail judgment doesn't need expensive reasoning |
| Steering Committee | 3 cheap, diverse models | Independent perspectives at minimal cost |
| Code Writer | Coding-specialized (e.g., Claude Code) | Needs tools, terminal access, test runners |
| Code Verifier | Different model family from Code Writer | Genuine independence — different training, different blind spots |

The key insight: **diversity matters more than quality** at each step. Three cheap, different models in the committee outperform one expensive model.

## State Management

All pipeline state lives in a single data directory:

```
~/.loopforge/           (configurable via LOOPFORGE_DATA_DIR)
├── backlog.md                    # Dynamic prioritized improvement list
├── current-proposals.json        # PM's current proposals
├── idea-verdicts.json            # Idea Verifier results
├── sprint-plan.json              # Committee's sprint plan
├── code-verdicts.json            # Code Verifier results
├── sprint-budget.json            # Budget tracking
├── cost-actuals.json             # Estimate vs actual costs
├── outcomes.json                 # Claimed vs measured impact
├── pm-context.json               # Feedback for next PM cycle
├── cycle-history.md              # Full cycle record
├── changelog.md                  # Every change committed
├── committee-evaluations/        # Individual member votes
├── script-baselines/             # Snapshots before modification
└── expert-directory.json         # Domain experts discovered
```

## Failure Modes

| Failure | Recovery |
|---------|----------|
| PM produces weak proposals | Idea Verifier catches and rejects them |
| Committee disagrees (no majority) | Proposal defers to next sprint |
| Code Writer produces bad code | Code Verifier catches and reverts |
| Code Verifier crashes (API error) | Engineering Phase falls back to manual verification |
| Budget exhausted | Remaining proposals wait for next sprint |
| Model provider down | Pipeline skips that step, logs the failure |

## Extending the System

### Adding a New Job to Improve

Add the job to the PM's inventory. The PM will naturally include it in future rotation.

### Adding a New Committee Member

Add a new model configuration to the Steering Committee. The voting logic supports any number of members — majority rules.

### Custom Auto-Ship Criteria

Modify the auto-ship criteria in the skill/spec. The current criteria are:
1. Cost < threshold
2. Idea Verifier rated research STRONG or ADEQUATE
3. Change affects only the target script
4. NOT security-sensitive
5. NOT modifying another cron job's behavior
6. NOT modifying the approval mechanism itself
7. NOT adding new external dependencies
8. NOT changing output format that other jobs consume
