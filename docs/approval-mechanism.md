# Approval Mechanism

LoopForge uses an asynchronous human-in-the-loop approval system. No job ever "waits" for the human — proposals are saved, notifications sent, and jobs exit.

## Architecture

```
Pipeline → encounters change → writes proposal
  → Sends notification to human
  → Job exits (no waiting)

Human approves/denies when available → response captured

Approval Processor cron (every 15m) → finds approved items → applies them
```

## Why Async?

The pipeline runs on a schedule (e.g., weekly). The human shouldn't have to be available at the exact moment the pipeline runs. The async pattern means:

- Pipeline runs to completion regardless of human availability
- Human reviews at their convenience
- Changes apply automatically once approved
- Proposals expire if not acted on (safety net)

## Directory Structure

```
approvals/
├── pending/       # Awaiting human approval
├── approved/      # Approved, waiting to be processed
├── denied/        # Denied by human
├── expired/       # Timed out (no response)
├── applied/       # Successfully applied
└── rollbacks/     # Rollback snapshots
```

## Interaction Pattern

### Approving a Change

The human says: "Approve apr-XXXXXX" (short ID)

The system:
1. Finds the matching proposal file
2. Reads it to confirm what the approval is for
3. Records the approval
4. Reports back what was approved

### Denying a Change

The human says: "Deny apr-XXXXXX — reason: ..."

The system records the denial with the reason. The reason feeds back to the PM so it doesn't repeat the pattern.

## Risk-Based Expiration

| Risk Level | Expiration | Rationale |
|-----------|------------|-----------|
| Critical | 24 hours | Data loss risk — act fast or forget it |
| High | 48 hours | Security changes — time-sensitive |
| Medium | 72 hours | Feature changes — reasonable window |
| Low | 7 days | Cosmetic fixes — low urgency |

If a proposal expires without action, it's moved to the expired folder and logged. The PM sees expired proposals and can re-evaluate whether they're still needed.

## Rollback Window

Every approved change has a rollback window of **3 runs** (configurable). The system captures a baseline before applying the change. If the change causes problems within the window, it can be reverted.

## Security-Sensitive Changes

These ALWAYS require explicit human approval, regardless of tier or committee vote:

- Firewall rule modifications
- DNS configuration changes
- SSH key/credential updates
- SSL/TLS certificate changes
- VLAN reconfigurations
- User permission/role changes
- Automated deployment of security policies

No exceptions. The committee can recommend, but only the human can approve these.
