"""LLM Gateway — Auth, Rate Limiting, Security, Cost Tracking, Routing."""
import hashlib
import os
import time
from collections import defaultdict

import httpx
from fastapi import FastAPI, HTTPException, Request
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from pydantic import BaseModel
from starlette.responses import Response

from security import run_security_checks, filter_pii

# --- Config ---
API_KEYS = set(os.getenv("GATEWAY_API_KEYS", "sk-demo-key-1").split(","))
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "60"))
COST_INPUT = float(os.getenv("COST_PER_INPUT_TOKEN", "0.000003"))
COST_OUTPUT = float(os.getenv("COST_PER_OUTPUT_TOKEN", "0.000015"))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
RAG_HOST = os.getenv("RAG_HOST", "http://rag:8001")

# --- Metrics ---
REQ_TOTAL = Counter("llm_requests_total", "Total LLM requests", ["endpoint", "status"])
REQ_LATENCY = Histogram("llm_request_duration_seconds", "Request latency", ["endpoint"])
TOKENS_TOTAL = Counter("llm_tokens_total", "Total tokens", ["direction"])
COST_TOTAL = Counter("llm_cost_dollars_total", "Total cost in dollars")
ACTIVE_KEYS = Gauge("llm_active_api_keys", "Number of active API keys")
ACTIVE_KEYS.set(len(API_KEYS))

# --- Rate Limiter (token bucket per key) ---
rate_state: dict = defaultdict(lambda: {"tokens": RATE_LIMIT_RPM, "last": time.time()})


def check_rate_limit(api_key: str) -> bool:
    state = rate_state[api_key]
    now = time.time()
    elapsed = now - state["last"]
    state["tokens"] = min(RATE_LIMIT_RPM, state["tokens"] + elapsed * (RATE_LIMIT_RPM / 60))
    state["last"] = now
    if state["tokens"] >= 1:
        state["tokens"] -= 1
        return True
    return False


# --- Auth ---
def verify_api_key(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing API key")
    key = auth[7:]
    if key not in API_KEYS:
        raise HTTPException(403, "Invalid API key")
    return key


# --- App ---
app = FastAPI(title="LLM Gateway")


class ChatRequest(BaseModel):
    message: str
    model: str = ""
    use_rag: bool = False


class ChatResponse(BaseModel):
    response: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    latency_ms: float


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    start = time.time()
    api_key = verify_api_key(request)

    if not check_rate_limit(api_key):
        REQ_TOTAL.labels(endpoint="chat", status="rate_limited").inc()
        raise HTTPException(429, "Rate limit exceeded")

    # Security checks
    security = run_security_checks(req.message)
    if not security.passed:
        REQ_TOTAL.labels(endpoint="chat", status="blocked").inc()
        raise HTTPException(400, f"Security check failed: {security.reason}")

    # PII filtering
    safe_message = filter_pii(req.message)
    model = req.model or OLLAMA_MODEL

    try:
        if req.use_rag:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(f"{RAG_HOST}/query", json={"question": safe_message})
                resp.raise_for_status()
                data = resp.json()
                answer = data["answer"]
                tokens_in = len(safe_message.split())
                tokens_out = len(answer.split())
        else:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json={"model": model, "prompt": safe_message, "stream": False},
                )
                resp.raise_for_status()
                data = resp.json()
                answer = data.get("response", "")
                tokens_in = data.get("prompt_eval_count", len(safe_message.split()))
                tokens_out = data.get("eval_count", len(answer.split()))
    except httpx.HTTPError as e:
        REQ_TOTAL.labels(endpoint="chat", status="error").inc()
        raise HTTPException(502, f"Backend error: {e}")

    cost = tokens_in * COST_INPUT + tokens_out * COST_OUTPUT
    latency = (time.time() - start) * 1000

    # Record metrics
    REQ_TOTAL.labels(endpoint="chat", status="ok").inc()
    REQ_LATENCY.labels(endpoint="chat").observe(latency / 1000)
    TOKENS_TOTAL.labels(direction="input").inc(tokens_in)
    TOKENS_TOTAL.labels(direction="output").inc(tokens_out)
    COST_TOTAL.inc(cost)

    return ChatResponse(
        response=answer, model=model,
        tokens_in=tokens_in, tokens_out=tokens_out,
        cost_usd=round(cost, 6), latency_ms=round(latency, 1),
    )


@app.get("/v1/models")
async def list_models():
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{OLLAMA_HOST}/api/tags")
        return resp.json()


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type="text/plain")


@app.get("/health")
def health():
    return {"status": "ok", "active_keys": len(API_KEYS)}
