# AGENTS.md

## Project Overview

Production-grade LLMOps platform lab — LLM Gateway, RAG Pipeline, AI Security middleware, and Observability stack. Built to demonstrate DevSecOps AI-Ready infrastructure skills.

## Tech Stack

- Python 3.11+ / FastAPI — gateway and RAG services
- Docker Compose — full stack orchestration
- PostgreSQL + pgvector — vector storage for RAG
- Ollama / vLLM — local LLM inference
- Prometheus + Grafana + Loki — monitoring
- GitHub Actions — CI

## Architecture

```
gateway/            → LLM Gateway (FastAPI): routing, auth, rate limiting, cost tracking
  main.py           → API endpoints
  security.py       → AI security layer (prompt guard, PII filter, input validation)
  Dockerfile
rag/                → RAG Service (FastAPI): embed, retrieve, generate
  main.py
  Dockerfile
monitoring/         → Prometheus config, Grafana dashboards, alert rules
models/             → Model configs
docs/               → AI_SECURITY_CHECKLIST.md, MLOPS_PIPELINE_SPEC.md
docker-compose.yml  → Full stack definition
setup-vm.sh         → VM provisioning script
.env.example        → Environment variable template
```

## Conventions

- Each service has its own `Dockerfile` and `requirements.txt`
- API endpoints follow RESTful patterns with `/docs` (Swagger)
- Security middleware applied at gateway level (not per-service)
- Environment config via `.env` file (never committed)
- Monitoring metrics exposed at `/metrics` endpoint

## Commands

- Start all: `docker compose up -d`
- Gateway docs: `http://localhost:8000/docs`
- RAG docs: `http://localhost:8001/docs`
- Grafana: `http://localhost:3000` (admin/admin)
- Prometheus: `http://localhost:9090`

## Security Rules

- All API keys hashed and rotatable
- Prompt injection detection enabled by default
- PII filtering before LLM calls
- Rate limiting per API key (token bucket)
- Never commit `.env` — use `.env.example` as template

## Important Notes

- Gateway port 8000, RAG port 8001, Ollama port 11434
- pgvector on port 5432 for vector similarity search
- Cost tracking per request (configurable $/token)
- Follows OWASP LLM Top 10 security guidelines
