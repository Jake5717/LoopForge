# Steering Committee — Architecture & Pitfalls

## Architecture (v2 — Dynamic Domain Experts)

### Member Roles

| Seat | Model | Fixed/Dynamic | Purpose |
|------|-------|---------------|---------|
| Budget Analyst | MiMo 2.5 | Fixed | Cost analysis, budget fit, value assessment |
| Risk Assessor | Gemini 2.5 Flash | Fixed | Blast radius, security, failure modes |
| Priority Arbitrator | GPT-4o Mini | Fixed | Impact, timing, opportunity cost, sprint packing |
| Domain Expert | Claude Haiku 4.5 | **Dynamic** | Changes per proposal based on target job |

### Dynamic Domain Expert Mapping

The 4th seat changes based on the proposal's `target_job`:

```python
DOMAIN_EXPERTS = {
    "ic-containers.py": "Senior SRE / Docker Infrastructure Specialist",
    "ic-resources.py": "Infrastructure / Capacity Planning Engineer",
    "ic-errors.py": "Observability / Monitoring Engineer",
    "network-guard.py": "Network Security Analyst",
    "Network Guard Analysis": "Threat Intelligence Analyst",
    "IC Morning Briefing": "SRE / Incident Response Lead",
    "Ward": "Governance / Compliance Auditor",
    "Scribe": "Knowledge Management Specialist",
    "LinkedIn Monitor": "Technical Recruiter / Career Strategist",
    "Discord Thread Renamer": "Community Manager",
    "Hermes & AI News": "AI/ML Research Analyst",
    "Guyana News": "Regional Analyst / Journalist",
    "Git Backup": "DevOps / Disaster Recovery Engineer",
    "loop-engineer": "SDLC / Process Improvement Expert",
}
```

**Why dynamic:** An SRE has no relevant opinion on meal planning or LinkedIn job matching. The expert must match the domain.

### Voting Rules

1. Each member votes: APPROVE / ESCALATE / DEFER
2. Majority wins
3. Tie → ESCALATE (safe default)
4. **Security override:** firewall_rule, dns_config, ssh_key, certificate, vlan_change, permission_change, credential_update → force ESCALATE regardless of votes
5. **Cost tier override:** cost_estimate >= $0.50 → force ESCALATE (medium tier requires [USER])

### Cost

~$0.002 per classification. Four cheap models, ~500 tokens each. $0.10/year.

## Pitfalls

### MiMo 2.5 Token Truncation
MiMo 2.5 truncates responses at ~1200 tokens. For structured JSON output (evaluations), use `max_tokens=2000+`. At 1200 tokens, the JSON gets cut mid-object, causing parse failures.

**Symptom:** Budget Analyst evaluations all show "Could not parse evaluation" while other models work fine.
**Fix:** Set `max_tokens=2000` in the API call.

### System Prompt Format Placeholders
System prompts with `{budget_remaining:.2f}` placeholders must be explicitly formatted before passing to models. Module-level string constants don't auto-format.

**Symptom:** Models receive literal `{budget_remaining:.2f}` in the prompt instead of actual values.
**Fix:** `system_prompt.format(**budget_ctx)` before passing to `call_model()`.

### JSON Parsing for Truncated Responses
Models (especially MiMo) may return truncated JSON. The parser needs three fallback layers:

1. **Strict JSON parse** — `json.loads()` on the full response
2. **Regex extraction** — `re.findall()` for individual `{"id": "prop-...", "vote": "...", "opinion": "..."}` objects
3. **Text inference** — Find proposal IDs in the response and extract nearby text

### Committee Placement
The Steering Committee sits **AFTER** the Idea Verifier, not before. Rationale:
- Idea Verifier is cheaper (Claude Sonnet ~$0.15) than Steering Committee analysis
- If Verifier rejects a proposal, don't waste budget-analyzing a bad idea
- Quality gate first, budget gate second

### Auto-Ship Criteria
ALL must be true for auto-ship:
1. Cost estimate < $0.50
2. Idea Verifier PASS
3. Only target script affected
4. Not security-sensitive type
5. Not modifying other cron jobs
6. Not modifying approval mechanism
7. No new dependencies
8. Not changing output format for other jobs

If ANY fails → escalate to [USER] even if minor.

### Prompt Design for Genuine Opinions
Don't write prompts that say "check these rules and vote." Write prompts that say "think about this from YOUR perspective and argue for your position."

**Bad:** "Check if cost < $0.50. If yes, vote APPROVE."
**Good:** "What's the cost-per-impact ratio? Is this worth the budget? What's the opportunity cost? Be opinionated."

Each member should have a distinct voice and perspective, not just apply the same rules differently.
