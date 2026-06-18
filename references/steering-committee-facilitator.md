# Steering Committee Facilitator — Post-Evaluation Workflow

## Trigger

This runs after `steering-committee.py evaluate` completes and writes `sprint-plan.json`.

## Pre-Steps (Before Running Evaluate)

1. **Merge idea verifier status into proposals:**
   ```python
   import json, os
   base = os.path.expanduser("~/.hermes/data/loop-engineer")
   with open(f"{base}/current-proposals.json") as f:
       proposals = json.load(f)
   with open(f"{base}/idea-verdicts.json") as f:
       verdicts = json.load(f)
   verdict_map = {v["id"]: v["status"] for v in verdicts}
   for p in proposals:
       if p["id"] in verdict_map:
           p["idea_verifier_status"] = verdict_map[p["id"]]
   with open(f"{base}/current-proposals.json", "w") as f:
       json.dump(proposals, f, indent=2)
   ```

2. **Ensure sprint-budget.json exists:**
   ```python
   import json, os
   from datetime import datetime, timezone
   budget_path = os.path.expanduser("~/.hermes/data/loop-engineer/sprint-budget.json")
   if not os.path.exists(budget_path):
       budget = {
           "sprint": datetime.now(timezone.utc).strftime("%Y-W%W"),
           "budget": 3.00, "spent": 0.00, "remaining": 3.00, "status": "active"
       }
       with open(budget_path, "w") as f:
           json.dump(budget, f, indent=2)
   ```

3. **Run evaluation:**
   ```bash
   python3 ~/.hermes/scripts/steering-committee.py evaluate
   ```

## Processing Results

Read `~/.hermes/data/loop-engineer/sprint-plan.json` for the three lists.

### Auto-Shipped Items

For each item in `sprint_plan["auto_ship"]`:

```bash
# 1. Create approval record
python3 ~/.hermes/scripts/approval-manager.py propose \
  --title "<title>" \
  --description "<description> [Steering Committee: <vote summary>]" \
  --risk <risk> \
  --type <type> \
  --proposed-by "steering-committee"

# 2. Immediately approve it
python3 ~/.hermes/scripts/approval-manager.py approve \
  --id <approval_id> \
  --approved-by "steering-committee" \
  --note "Auto-approved: <vote breakdown>"
```

### Escalated Items

For each item in `sprint_plan["escalate"]`:

```bash
python3 ~/.hermes/scripts/approval-manager.py propose \
  --title "<title>" \
  --description "<description> [Steering Committee: <reason for escalation>]" \
  --risk <risk> \
  --type <type> \
  --proposed-by "steering-committee"
```

Leave as pending — [USER] will approve/deny.

### Deferred Items

For each item in `sprint_plan["defer"]`:

Add to `~/.hermes/data/loop-engineer/improvement-backlog.md` under the appropriate job section:

```markdown
- ⏳ DEFERRED (YYYY-WNN): <title> [prop-NNN] — ROI X.Xx, $N.NN. <vote summary>. Next sprint candidate.
```

### Update Budget

```python
import json, os
path = os.path.expanduser("~/.hermes/data/loop-engineer/sprint-budget.json")
with open(path) as f:
    budget = json.load(f)
auto_cost = sum(e.get("cost_estimate", 0) for e in sprint_plan["auto_ship"])
budget["spent"] = auto_cost
budget["remaining"] = budget["budget"] - auto_cost
with open(path, "w") as f:
    json.dump(budget, f, indent=2)
```

## Summary Report

Send to [USER] with:
- **Auto-shipping:** What + why (committee rationale)
- **Escalated:** What + vote breakdown + expiration date
- **Deferred:** What + why (committee rationale)
- **Budget:** Total, spent, remaining, pending escalation cost

## Known Issues

- **Budget Analyst (MiMo 2.5) parse failures:** MiMo frequently returns unparseable JSON. The script has 3 fallback strategies but all can fail. If consistent, consider: (a) fewer proposals per batch, (b) shorter system prompt, (c) swapping model.
- **No auto-ship subcommand:** `steering-committee.py` only has `evaluate` and `status`. Auto-ship is processed via `approval-manager.py` (create + immediate approve).
- **Forced escalation:** Items with cost ≥ $0.50 or security-sensitive types are force-escalated regardless of votes. The committee votes are overridden to ESCALATE.
