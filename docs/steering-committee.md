# Steering Committee

The Steering Committee is the governance layer of LoopForge. Three independent AI models evaluate every proposal before it touches code.

## Members

| Member | Role | Evaluates |
|--------|------|-----------|
| **Budget Analyst** | Financial gatekeeper | Cost realism, value credibility, ROI, opportunity cost |
| **Risk Assessor** | Risk evaluator | Blast radius, security implications, failure modes, dependencies |
| **Priority Arbitrator** | Strategic prioritizer | Impact, timing, leverage, ROI, opportunity cost |

## Why Three Members

1. **Diversity of perspective** — Each member evaluates through a different lens
2. **No single point of failure** — One bad evaluation doesn't kill good proposals
3. **Genuine debate** — Independent evaluation before comparison prevents groupthink
4. **Cost-effective** — Three cheap models cost less than one expensive one

## Voting Process

### Step 1: Independent Evaluation

Each member reads all proposals and evaluates independently. They don't see each other's evaluations.

### Step 2: Classification

Each member classifies each proposal as:
- **SHIP** — Approve for auto-implementation
- **ESCALATE** — Needs human approval
- **DEFER** — Push to next sprint

### Step 3: Majority Vote

The outcome is determined by majority vote:
- **2+ SHIP** → Auto-ship (if all auto-ship criteria met)
- **2+ ESCALATE** → Escalate to human
- **2+ DEFER** → Defer to next sprint

### Step 4: Forced Escalation

Some items are force-escalated regardless of vote:
- **Security-sensitive changes** (firewall, DNS, SSH, certs, permissions)
- **Medium-tier items** (cost ≥ $0.50)
- **Cross-cutting changes** (affects multiple scripts)

When force-escalating, the original member analyses are preserved — the human needs the full picture.

## Cost Tiers

| Tier | Cost Estimate | Decision | Examples |
|------|--------------|----------|----------|
| Minor | < $0.50 | Auto-ship (if criteria met) | New output field, better error message |
| Medium | $0.50–1.50 | Escalate to human | New detection logic, changed thresholds |
| Major | > $1.50 | Escalate, may break down | New script, new integration |

## Auto-Ship Criteria

ALL of the following must be true for auto-ship:

1. Cost estimate < $0.50 (minor tier)
2. Idea Verifier rated research STRONG or ADEQUATE
3. Change affects only the target script (no cross-cutting)
4. NOT security-sensitive (firewall, DNS, SSH, certs, VLAN, permissions)
5. NOT modifying another job's behavior
6. NOT modifying the approval mechanism itself
7. NOT adding new external dependencies
8. NOT changing output format that other jobs consume

If ANY criterion fails, the item is escalated even if it's minor.

## Budget Directive

The committee should spend the full weekly budget each round. Items with low ROI should still be auto-shipped if they fit within the remaining budget. Low ROI ≠ no value. Only defer if the cost actually exceeds the remaining budget.

## Output Format

The committee produces a sprint plan:

```json
{
  "auto_ship": [
    {"id": "prop-001", "title": "...", "estimated_cost": 0.40, "votes": {"budget": "SHIP", "risk": "SHIP", "priority": "SHIP"}}
  ],
  "escalate": [
    {"id": "prop-003", "title": "...", "estimated_cost": 0.80, "votes": {"budget": "ESCALATE", "risk": "ESCALATE", "priority": "ESCALATE"}}
  ],
  "defer": [
    {"id": "prop-005", "title": "...", "estimated_cost": 0.30, "votes": {"budget": "DEFER", "risk": "DEFER", "priority": "DEFER"}}
  ],
  "budget_status": {"total": 3.00, "spent": 1.20, "remaining": 1.80}
}
```

## Facilitation

After the committee evaluates, a facilitator processes the results:

1. **Auto-shipped items** → Record approval in the system
2. **Escalated items** → Queue for human review with full vote breakdown
3. **Deferred items** → Add to backlog with explanation
4. **Update budget** → Reflect auto-shipped costs
5. **Send summary** → Report to the human operator
