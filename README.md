# LoopForge

**AI agents that improve other AI agents — automatically, every week.**

LoopForge is a self-improving Kaizen pipeline where multiple AI models research, review, debate, and implement improvements to your automation scripts and cron jobs. No single model grades its own homework — every step uses a different model from a different provider for genuine independence.

## The Problem

Here's the thing — **you don't know what you don't know.**

When you build a script, a cron job, or an AI agent to do something useful, you're building it with the best of *your* ability. You add the features you think of. You handle the edge cases you've seen before. You build it as well as you can, and you deploy it.

But what about the things an experienced practitioner would catch? The best practices you've never read about? The failure modes you haven't hit yet? That gap — between what you built and what an expert would build — just sits there. Forever.

LoopForge closes that gap. Not by making you smarter, but by **building a team of AI agents that research, review, debate, and improve your work — every week.**

## How It Works

LoopForge is a 6-step pipeline. Each step uses a different AI model. No step grades its own homework.

```
┌──────────────────────────────────────────────────────────┐
│  STEP 1: Product Manager (Research Model)                │
│  Reviews ALL jobs + backlog → picks 3-5 to improve       │
│  Researches what experts actually do → writes proposals   │
└──────────────────────┬───────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 2: Idea Verifier (Different Model)                 │
│  "Is this research real or shallow?"                     │
│  Rates quality: STRONG / ADEQUATE / WEAK                 │
│  Can kill proposals before any code is written            │
└──────────────────────┬───────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 3: Steering Committee (3 Independent Models)       │
│  Budget Analyst: "Is this worth the cost?"               │
│  Risk Assessor:  "What could go wrong?"                   │
│  Priority Arb:   "Is this the best use of our budget?"   │
│  Majority vote → auto-ship / escalate / defer            │
└──────────────────────┬───────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 4: Code Writer (Coding Model — e.g. Claude Code)   │
│  Implements ONLY approved items. Nothing extra.           │
│  Full terminal access — reads code, makes the change.     │
└──────────────────────┬───────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 5: Code Verifier (Different Model Family)          │
│  Adversarial code review: bugs, edge cases, scope creep  │
│  If it fails → change reverts. Period.                    │
└──────────────────────┬───────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 6: Engineering Phase                               │
│  Commit → Changelog → State updates → Rollback snapshot  │
│  Every change documented: what, why, who, how to undo.   │
└──────────────────────────────────────────────────────────┘
```

### Why Each Step Is Isolated

The biggest insight: **no single AI model should grade its own homework.**

Every step uses a different AI model from a different company with different training data. The model that *writes* the code is not the same model that *reviews* it. The model that *researches* improvements is not the same model that *decides* whether they're worth doing.

This is exactly how peer review works in science, code review in engineering, and audit in finance.

### The Steering Committee

Three independent AI models evaluate every proposal before it touches code:

| Member | Evaluates |
|--------|-----------|
| **Budget Analyst** | Cost realism, value credibility, ROI, opportunity cost |
| **Risk Assessor** | Blast radius, security implications, failure modes, dependencies |
| **Priority Arbitrator** | Impact, timing, leverage, ROI, opportunity cost |

Each member thinks independently. Majority vote decides the outcome. Security-sensitive changes always escalate to the human — no exceptions.

## Safety Rails

| Feature | Description |
|---------|-------------|
| 🔒 **Auto-ship** | Small fixes (< $0.50, no security impact) ship automatically |
| ✋ **Human approval** | Risky changes always come to you for approval |
| ⏪ **Rollback window** | Every change gets a snapshot. Problems within 3 runs → auto-revert |
| 📋 **Full audit trail** | Every change logged: what, why, who reviewed, which models |
| 💰 **Budget cap** | Weekly budget prevents runaway costs (~$3/week) |

## Feedback Loops

The system doesn't just improve your tools — it improves *itself*:

1. **Cost tracking** — The PM estimates costs. After shipping, the system compares estimate vs. actual. The PM learns to estimate better.
2. **Outcome measurement** — The PM claims "this will save X min/week." Monthly verification checks if it actually did.
3. **Committee feedback** — Rejections and deferrals feed back to the PM so it doesn't repeat mistakes.

## Quick Start

### Prerequisites

- Python 3.10+
- API access to at least 2 LLM providers (for model diversity)
- A target system with scripts/jobs to improve

### Installation

```bash
git clone https://github.com/Jake5717/LoopForge.git
cd LoopForge
pip install -r requirements.txt  # coming soon
```

### Configuration

Set environment variables for your LLM providers:

```bash
export OPENROUTER_API_KEY="your-key-here"
# Add other provider keys as needed
```

### Usage

```bash
# Run the full pipeline
python scripts/steering-committee.py evaluate

# Check status
python scripts/steering-committee.py status

# Track costs
python scripts/pipeline-tracker.py cost-report

# Submit feedback
python scripts/loop-engineer-feedback.py --feedback "The monitoring script missed X"
```

## Project Structure

```
LoopForge/
├── README.md                    ← You are here
├── LOOPFORGE-SPEC.md            ← Full pipeline specification
├── docs/
│   ├── architecture.md          ← System architecture deep-dive
│   ├── steering-committee.md    ← Committee design and voting logic
│   ├── approval-mechanism.md    ← Async human-in-the-loop approvals
│   └── cost-model.md            ← Budget tiers, ROI analysis, cost tracking
├── scripts/
│   ├── steering-committee.py    ← Multi-model proposal evaluation
│   ├── approval-manager.py      ← Async approval workflow
│   ├── approval-processor.py    ← Applies approved changes
│   ├── pipeline-tracker.py      ← Cost tracking + outcome measurement
│   └── feedback-ingest.py       ← Backlog ingestion from feedback
├── references/
│   ├── architecture-decisions.md
│   ├── governance-model.md
│   ├── pilot-results.md
│   └── ... (13 more design docs)
├── design/
│   ├── design-v1.md             ← Original design document
│   ├── design-v2.md             ← Evolved design with committee
│   ├── workflow.md               ← Step-by-step workflow
│   └── loop-engineer-workflow.excalidraw
└── LICENSE
```

## Design Documents

The `references/` directory contains the full design history — from initial concept through pilot results. Key docs:

- **[Architecture Decisions](references/architecture-decisions.md)** — Why we chose multi-model over single-model, why 6 steps instead of 4
- **[Governance Model](references/governance-model.md)** — How the Steering Committee classifies and routes proposals
- **[Pilot Results](references/pilot-results.md)** — What happened when we actually ran the pipeline
- **[Idea Verifier Cost Incident](references/idea-verifier-cost-incident.md)** — Real incident where using the wrong model burned $5 in 2 days

## The Vision

LoopForge starts as an internal operations tool, but the pattern is universal:

- **SRE teams** — Monitoring scripts that improve themselves after every incident
- **DevOps** — CI/CD pipelines that learn from false positives
- **Security** — Threat detection that adapts to new attack patterns
- **Product teams** — Feature flags and A/B tests that optimize themselves

This is **Kaizen for the AI era** — continuous improvement, but instead of humans doing it, AI agents do it for you. And the governance layer means you never lose control.

## Cost

~$1.50–2.50 per weekly cycle (with 3–5 proposals). ~$80–130/year.

| Step | Model | ~Cost/Cycle |
|------|-------|-------------|
| PM | Research-optimized model | ~$0.25 |
| Idea Verifier | Fast/cheap model (e.g. Gemini Flash) | ~$0.05 |
| Steering Committee | 3 cheap models (parallel) | ~$0.15 |
| Code Writer | Coding model (e.g. Claude Code) | ~$0.60 |
| Code Verifier | Different model family (e.g. GPT-4o) | ~$0.25 |

## License

MIT — use it, fork it, improve it.

---

*Built with [Hermes Agent](https://hermes-agent.nousresearch.com) · Powered by 5+ AI models working together*

*"I don't know what I don't know — so I hired a team that does."*
