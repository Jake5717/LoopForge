# Steering Committee Design — v2 (June 13, 2026)

## Architecture

4-member committee with dynamic domain expertise. Runs after Idea Verifier, before Code Writer.

### Members

| Seat | Model | Provider | Fixed/Dynamic |
|------|-------|----------|---------------|
| Budget Analyst | MiMo 2.5 | Xiaomi | Fixed |
| Risk Assessor | Gemini 2.5 Flash | OpenRouter | Fixed |
| Priority Arbitrator | GPT-4o Mini | OpenRouter | Fixed |
| Domain Expert | Claude Haiku 4.5 | OpenRouter | **Dynamic** |

### Dynamic Domain Expert

The 4th seat changes based on the proposal's `target_job`:

- container-monitor.py → Senior SRE / Docker Specialist
- error-scanner.py → Observability / Monitoring Engineer
- network-guard.py → Network Security Analyst
- Product Research → Market Research / Competitive Analyst
- Ward → Governance / Compliance Auditor
- Loop Engineer → SDLC / Process Improvement Expert
- ... (14 jobs mapped, see script for full list)

### Voting

- Each member votes: APPROVE / ESCALATE / DEFER
- Majority wins, tie → ESCALATE
- Security-sensitive types → force ESCALATE
- Cost >= $0.50 → force ESCALATE (medium tier)

### Budget

- $3/week sprint budget
- Auto-ship minor items (< $0.50) that meet ALL 8 criteria
- Escalate medium/major items to [USER] via approval mechanism
- Defer items exceeding budget

### Auto-Ship Criteria (ALL must be true)

1. Cost < $0.50
2. Idea Verifier PASS
3. Only target script affected
4. Not security-sensitive
5. Not modifying other cron jobs
6. Not modifying approval mechanism
7. No new dependencies
8. Not changing output format for other jobs

### Cost

~$0.002 per classification. $0.10/year.

## Pipeline Flow

```
PM (V2.5 Pro) → 3-5 proposals
  → Idea Verifier (Claude Sonnet) → PASS/FAIL each
  → Steering Committee (4 cheap models) → Vote: auto-ship / escalate / defer
  → Code Writer (Claude Code) → implements auto-shipped items only
  → Code Verifier (GPT-4o) → adversarial review
  → Engineering Phase (V2.5 Pro) → commit + changelog
  → Approval Processor (cron) → applies [USER]-approved items
```

## Key Decisions

1. Steering Committee after Idea Verifier — quality gate before budget gate
2. Dynamic domain experts — hardcoded SRE was too narrow for 14 different jobs
3. Genuine opinions, not rule-checking — prompts ask for analysis and perspective
4. Cheap models for classification — MiMo 2.5, Gemini Flash, GPT-4o Mini, Claude Haiku
5. Security override — force-escalate regardless of votes
6. Cost tier override — >= $0.50 force-escalate
7. Conservative auto-ship — expand criteria over time as trust builds
