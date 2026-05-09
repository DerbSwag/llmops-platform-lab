"""RAG Service — Embed, Store, Retrieve, Generate."""
import os
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, UploadFile
from prometheus_client import Counter, Histogram, generate_latest
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import psycopg2
from pgvector.psycopg2 import register_vector

# --- Config ---
PG_DSN = (
    f"host={os.getenv('POSTGRES_HOST', 'postgres')} "
    f"port={os.getenv('POSTGRES_PORT', '5432')} "
    f"dbname={os.getenv('POSTGRES_DB', 'ragdb')} "
    f"user={os.getenv('POSTGRES_USER', 'raguser')} "
    f"password={os.getenv('POSTGRES_PASSWORD', 'changeme')}"
)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# --- Metrics ---
EMBED_COUNT = Counter("rag_embeddings_total", "Total embeddings created")
QUERY_COUNT = Counter("rag_queries_total", "Total RAG queries")
QUERY_LATENCY = Histogram("rag_query_duration_seconds", "RAG query latency")

# --- App ---
embedder = None
conn = None


def init_db():
    global conn
    conn = psycopg2.connect(PG_DSN)
    register_vector(conn)
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding vector(384),
                metadata JSONB DEFAULT '{}'
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_docs_embedding
            ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10)
        """)
    conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global embedder
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    init_db()
    yield
    if conn:
        conn.close()


app = FastAPI(title="RAG Service", lifespan=lifespan)


# --- Models ---
class IngestRequest(BaseModel):
    text: str
    metadata: dict = {}


class QueryRequest(BaseModel):
    question: str
    top_k: int = 3


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    latency_ms: float


# --- Helpers ---
def chunk_text(text: str) -> list[str]:
    chunks = []
    for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
        chunk = text[i : i + CHUNK_SIZE]
        if chunk.strip():
            chunks.append(chunk.strip())
    return chunks


async def generate(prompt: str, context: str) -> str:
    system = "Answer based on the provided context. If unsure, say so."
    full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": full_prompt, "system": system, "stream": False},
        )
        resp.raise_for_status()
        return resp.json().get("response", "")


# --- Endpoints ---
@app.post("/ingest")
def ingest(req: IngestRequest):
    chunks = chunk_text(req.text)
    embeddings = embedder.encode(chunks).tolist()
    with conn.cursor() as cur:
        for chunk, emb in zip(chunks, embeddings):
            cur.execute(
                "INSERT INTO documents (content, embedding, metadata) VALUES (%s, %s, %s)",
                (chunk, emb, psycopg2.extras.Json(req.metadata)),
            )
    conn.commit()
    EMBED_COUNT.inc(len(chunks))
    return {"chunks_stored": len(chunks)}


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    start = time.time()
    QUERY_COUNT.inc()

    q_embedding = embedder.encode([req.question])[0].tolist()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT content, 1 - (embedding <=> %s::vector) AS score "
            "FROM documents ORDER BY embedding <=> %s::vector LIMIT %s",
            (q_embedding, q_embedding, req.top_k),
        )
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(404, "No documents found. Ingest data first.")

    context = "\n---\n".join(r[0] for r in rows)
    answer = await generate(req.question, context)
    latency = (time.time() - start) * 1000

    QUERY_LATENCY.observe(latency / 1000)
    return QueryResponse(answer=answer, sources=[r[0][:100] for r in rows], latency_ms=round(latency, 1))


@app.get("/metrics")
def metrics():
    from starlette.responses import Response
    return Response(content=generate_latest(), media_type="text/plain")


@app.get("/health")
def health():
    return {"status": "ok"}
