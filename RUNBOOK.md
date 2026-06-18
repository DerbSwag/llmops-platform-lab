# RUNBOOK — llmops-platform-lab

> Procedures for Production-grade MLOps/LLMOps Lab
> Updated: 2026-06-15

## Quick Reference

| Item | Value |
|------|-------|
| Stack | Python, Docker, Prometheus, Grafana |
| Components | LLM Gateway, RAG Pipeline, AI Security, Monitoring |
| Purpose | DevSecOps AI-Ready lab |

---

## Procedures

### 1. Start All Services

```bash
docker compose up -d
```

### 2. LLM Gateway Health Check

```bash
curl http://localhost:8000/health
```

### 3. RAG Pipeline Test

```bash
python test_rag.py --query "test question"
```

### 4. Monitoring Access

- Grafana: `http://localhost:3000` (admin/admin)
- Prometheus: `http://localhost:9090`

### 5. Troubleshooting

| Symptom | Fix |
|---------|-----|
| Gateway timeout | Check LLM provider API key, rate limits |
| RAG returns empty | Verify vector DB is populated, check embedding service |
| Prometheus no targets | Verify service_discovery in prometheus.yml |
| OOM | Increase Docker memory limit |

---

## Secrets & Security

- LLM API keys: `.env` file (gitignored)
- ห้าม commit: API keys, model weights, user data

---

## Related Docs

- `README.md` — architecture and setup
