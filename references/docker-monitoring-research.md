# Container Monitoring — Research Findings (Cycle 1)

**Date:** 2026-06-12
**Source:** Loop Engineer Cycle 1 research for container-monitor.py
**Experts consulted:** Last9, Dockmon, Xitoring, Dash0, Grizzly Peak Software

## Top Insights

### 1. "Running" ≠ "Healthy" — Crash Loops Are Invisible

A container can be "Up 2 minutes" right now but have restarted 20 times in the last hour. Every major monitoring tool (Datadog, Prometheus, cAdvisor) tracks `RestartCount` as a primary stability signal.

**Detection approach:** `docker inspect --format '{{.RestartCount}}|{{.State.FinishedAt}}' <container>`

**Threshold pattern:** Alert when RestartCount > N AND last restart within time window. This prevents false positives from historical restarts over long uptimes.

- Dockmon uses: max 3 restarts per 10 minutes
- Our implementation: >3 restarts within 1 hour

### 2. Time-Windowed Thresholds Prevent False Positives

A container that restarted 5 times over 6 months is fine. One that restarted 5 times in 10 minutes is crash-looping. Always pair a count threshold with a recency check.

### 3. Docker Exposes Restart Data Natively

`docker inspect` provides RestartCount and FinishedAt with zero dependencies. No cAdvisor, no Prometheus, no sidecar containers needed. One SSH call per container.

### 4. Docker Timestamps Are Non-Trivial

Docker uses RFC 3339 with nanosecond precision: `2026-06-12T10:30:00.123456789Z`

Python's `datetime.fromisoformat()` only handles microseconds (6 digits). Solution: truncate the fractional seconds to 6 digits before parsing.

Also handle the zero-time sentinel: `0001-01-01T00:00:00Z` means "never finished."

### 5. Health Check Hierarchy

Production monitoring tools check at three levels:
1. **Process alive** — is the container running? (what container-monitor.py already checks)
2. **Health check passing** — does Docker's HEALTHCHECK report healthy? (container-monitor.py catches "unhealthy")
3. **Service responding** — is the application actually serving requests? (gap — requires HTTP/TCP probes)

## Sources

| Source | Focus Area | URL |
|--------|-----------|-----|
| Last9 | Restart count as stability signal | https://last9.io/blog/best-container-monitoring-tools/ |
| Dockmon | Rate-limited restart policies | https://github.com/darthnorse/dockmon/wiki/Health-Checks |
| Xitoring | CPU/memory/restart tracking | https://xitoring.com/blog/what-is-docker-container-monitoring |
| Dash0 | HEALTHCHECK vs process status | https://www.dash0.com/guides/docker-health-check-a-practical-guide |
| Grizzly Peak | Liveness vs readiness probes | https://www.grizzlypeaksoftware.com/library/health-checks-in-docker-and-kubernetes-tnmq6wr6 |
