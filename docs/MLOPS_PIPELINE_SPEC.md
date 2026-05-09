# MLOps / LLMOps Pipeline Specification

## Overview

This document describes the end-to-end pipeline for deploying, serving, and monitoring LLM-based applications in production.

---

## Pipeline Stages

```text
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Develop │───▶│  Build   │───▶│  Test    │───▶│  Deploy  │───▶│  Monitor │
│          │    │          │    │          │    │          │    │          │
│ - Code   │    │ - Docker │    │ - Lint   │    │ - Canary │    │ - Metrics│
│ - Prompt │    │ - CI     │    │ - Unit   │    │ - Blue/  │    │ - Cost   │
│ - Config │    │          │    │ - Integ  │    │   Green  │    │ - Alerts │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## 1. Development

| Artifact | Storage | Versioning |
|----------|---------|-----------|
| Application code | Git (GitHub) | Semantic versioning |
| Prompts / System messages | Git (version-controlled) | Tagged releases |
| Model configs | Git + .env | Environment-specific |
| RAG documents | PostgreSQL + pgvector | Timestamped ingestion |

## 2. Build (CI)

**Trigger:** Push to `main` or PR

| Step | Tool | Purpose |
|------|------|---------|
| Lint | Ruff | Code quality |
| Secret scan | detect-secrets | Prevent credential leaks |
| Unit tests | pytest | Logic validation |
| Docker build | Docker | Image creation |
| Image scan | Trivy | Vulnerability detection |
| Compose validation | docker compose config | Config correctness |

## 3. Testing

| Test Type | Scope | Automation |
|-----------|-------|-----------|
| Unit | Security module, helpers | CI (every push) |
| Integration | Gateway → Ollama → Response | CI (with docker compose) |
| Load | Concurrent requests, rate limiting | Manual / scheduled |
| Security | Prompt injection attempts | CI (test suite) |
| Eval | LLM response quality (optional) | Manual / A-B testing |

## 4. Deployment Strategy

### Blue-Green (recommended for LLM services)

```text
                    ┌─────────────────┐
                    │   Load Balancer  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼                             ▼
    ┌─────────────────┐          ┌─────────────────┐
    │  Blue (current)  │          │  Green (new)     │
    │  Gateway v1.0    │          │  Gateway v1.1    │
    │  RAG v1.0        │          │  RAG v1.1        │
    └─────────────────┘          └─────────────────┘
```

**Rollback:** Switch traffic back to Blue in < 30 seconds.

### Canary (for model changes)

- Route 5% traffic to new model
- Monitor: latency, error rate, cost
- If metrics OK after 30 min → promote to 100%
- If degraded → auto-rollback

## 5. Monitoring & Observability

### Metrics (Prometheus)

| Metric | Type | Alert Threshold |
|--------|------|----------------|
| `llm_requests_total` | Counter | Error rate > 10% |
| `llm_request_duration_seconds` | Histogram | P95 > 10s |
| `llm_tokens_total` | Counter | — |
| `llm_cost_dollars_total` | Counter | > $50/day |
| `rag_queries_total` | Counter | — |
| `rag_query_duration_seconds` | Histogram | P95 > 5s |

### Dashboards (Grafana)

1. **LLM Overview** — RPS, latency, error rate, active models
2. **Cost Tracker** — Token usage, cost per key, daily/weekly trends
3. **RAG Performance** — Query latency, cache hits, document count
4. **Security** — Blocked requests, injection attempts, rate limit hits

### Alerting

| Severity | Condition | Action |
|----------|-----------|--------|
| Critical | Cost > budget | Auto-disable non-essential keys |
| Warning | P95 > 10s | Page on-call |
| Warning | Error rate > 10% | Slack notification |
| Info | New model deployed | Log only |

## 6. Cost Management

```text
Cost = (input_tokens × $0.000003) + (output_tokens × $0.000015)
```

Controls:
- Per-key daily budget limits
- Alert at 80% budget consumption
- Auto-disable at 100%
- Monthly cost reports per team/project

---

## Infrastructure Requirements

| Component | Min Resources | Production |
|-----------|--------------|-----------|
| Gateway | 1 CPU, 512MB | 2 CPU, 1GB (HA: 2 replicas) |
| RAG Service | 2 CPU, 2GB | 4 CPU, 4GB (embedding model) |
| Ollama | 4 CPU, 8GB | GPU instance (A10/T4) |
| PostgreSQL | 1 CPU, 1GB | 2 CPU, 4GB (SSD) |
| Prometheus | 1 CPU, 1GB | 2 CPU, 4GB (retention: 30d) |
| Grafana | 0.5 CPU, 256MB | 1 CPU, 512MB |
