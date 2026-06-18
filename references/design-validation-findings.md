# Design Validation Research Findings (Cycle 0)

Date: 2026-06-12
Sources: 20+ articles on loop engineering, multi-agent systems, self-improving agents

## Key Findings That Changed the Design

### 1. Three agents → Two agents
**Source:** Anthropic multi-agent research system (June 2025)
- Agents with vague, overloaded instructions "duplicate work, leave gaps, or fail to find necessary information"
- Research and implementation are naturally coupled — can't implement well without understanding domain
- Fewer coordination points = fewer failure modes

### 2. Token budgets are mandatory, not optional
**Source:** Production agent cost control data (2026)
- 68% of teams hit budget overruns in first deployments
- 50% cite "runaway tool loops and recursive logic" as the cause
- Multi-agent systems use ~15x more tokens than chats (Anthropic data)
- Single agent tasks can consume $500+ without budget limits

### 3. Research must be scoped
**Source:** Loop engineering best practices (Osmani, Steinberger, Cherny)
- "Find experts, read everything" → unscoped research burns tokens without producing improvements
- Solution: pre-written research briefs with specific questions, sources, and "useful finding" criteria
- Token budget per research phase (10K tokens typical)

### 4. Stop conditions prevent improvement churn
**Source:** Self-improving agent patterns (Agenthub, April 2026)
- Without stop conditions, loops keep making changes that don't add up
- Solution: quality thresholds + "two consecutive cycles with no improvement = done"
- Same as convergence stall in builder/auditor pattern

### 5. Objectives kernel prevents goal drift
**Source:** Self-improving agent patterns (Agenthub, April 2026)
- Read-only top-level goals stored outside the agent's mutable state
- Agent reads at start of every cycle, any violation = reject before implementation
- Same pattern as "Objective Kernel" in production agent systems

### 6. Measurement must be objective
**Source:** Agent evaluation best practices (Google Cloud, Anthropic)
- "Done" must mean something verifiable, not "it feels better"
- Before/after baseline comparison is the minimum viable measurement
- LLM-as-judge evaluation scales when done well (single call, rubric, 0.0-1.0 score)

### 7. Maker-checker is the critical pattern
**Source:** Every production system reviewed
- Anthropic: "The single most useful structural move in a loop is splitting the agent that writes from the agent that checks"
- Claude Code /goal: separate model decides if loop is done, not the one that did the work
- Every loop engineering guide emphasizes this as the fundamental pattern

## Sources Consulted

### Primary
- Lushbinary: "Loop Engineering: The Guide for AI Agents" (June 2026)
- Anthropic: "How we built our multi-agent research system" (June 2025)
- Agenthub: "7 Patterns for Self-Improving AI Agents" (April 2026)
- Cost Control & Token Budgets (Production Agents deep dive)

### Supporting
- Addy Osmani: Loop Engineering / Agent Harness Engineering
- Peter Steinberger: OpenClaw checklist
- Boris Cherny: Claude Code architecture
- Google Cloud: Production-ready AI agents guide
- OpenAI: Self-Evolving Agents Cookbook
- Microsoft: AgentOps lifecycle management
