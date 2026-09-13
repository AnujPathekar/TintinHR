# TintinHR — Authorization-Aware Agentic HR Assistant

TintinHR is a production-style HR portal and AI assistant. It combines policy-document RAG with employee-specific PostgreSQL data, routes requests through a LangGraph workflow, enforces access control before retrieval, cites sources, and refuses unsupported answers.

## Why this is more than a PDF chatbot

- Structured + unstructured retrieval: employee/leave data from SQL and policy knowledge from documents.
- Authorization-aware RAG: role, department, confidentiality and document lifecycle filters are applied inside retrieval—not after generation.
- Hybrid retrieval: PostgreSQL full-text search + pgvector, reciprocal-rank fusion, optional cross-encoder reranking.
- Agentic workflow: classifies intent, rewrites contextual questions, selects policy/employee/hybrid tools, validates grounding and persists the conversation.
- Production foundations: JWT token pairs, RBAC, audit events, authorization-partitioned Redis caching/rate limits, Celery ingestion, document versioning, citations, evaluation, tracing, Docker, tests and CI.

## Stack

| Layer | Technology |
|---|---|
| Portal | Next.js, TypeScript, Tailwind CSS |
| API | Python, FastAPI, Pydantic, SQLAlchemy async |
| Agent | LangGraph + provider-neutral LLM adapter |
| Retrieval | PostgreSQL 16, pgvector, native FTS, RRF, CrossEncoder |
| Operations | Redis, Celery, LangSmith-compatible tracing |
| Quality | Pytest, Vitest, Ruff, MyPy, evaluation dataset |

## Run locally with Docker

1. Copy `.env.example` to `.env`. The default uses Ollama; either run `ollama pull llama3.1:8b` or configure another provider.
2. Start all services:

   ```bash
   docker compose up --build
   ```

3. Seed demo users and HR data:

   ```bash
   docker compose exec api python -m app.db.seed
   docker compose exec api python -m app.db.seed_documents
   ```

4. Open `http://localhost:3000`. API documentation is at `http://localhost:8000/docs`.

Demo passwords are printed by the seed command and are intended only for local development.

## Provider configuration

| Provider | `LLM_PROVIDER` | Example model | Other settings |
|---|---|---|---|
| Ollama | `ollama` | `llama3.1:8b` | `LLM_BASE_URL=http://host.docker.internal:11434/v1` |
| OpenAI | `openai` | `gpt-4.1-mini` | `LLM_API_KEY` |
| Groq | `groq` | `llama-3.3-70b-versatile` | `LLM_API_KEY` |
| Gemini | `gemini` | `gemini-2.0-flash` | `LLM_API_KEY` |

Embeddings default to `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). When changing the embedding model, update `EMBEDDING_DIMENSION`, recreate the migration/type, and re-index documents.

## Main flows

### Document ingestion

Admin upload → MIME/size validation → SHA-256 duplicate check → version record → Celery job → parse → page-aware chunks → embeddings → pgvector → active index.

### Answer generation

Authenticated question → conversation-aware rewrite → intent/router → authorized SQL and/or policy retrieval → hybrid fusion → reranking → context budget → generation → citation validation → groundedness check → safe response → persisted trace.

## API highlights

- `POST /api/v1/auth/login`, `POST /auth/refresh`
- `POST /api/v1/chat`, `GET /conversations`
- `POST /api/v1/documents`, `GET/PATCH/DELETE /documents/{id}` (HR/Admin)
- `GET /api/v1/employees/me`, `GET /employees/me/leave`
- `GET /api/v1/admin/metrics`, `GET /admin/audit-events`

## Evaluation

Run `make eval` after seeding and indexing documents. The evaluation suite records:

- retrieval hit rate / context precision proxy;
- answer relevancy;
- citation validity;
- groundedness/faithfulness;
- abstention correctness;
- p50/p95 latency and token usage.

See [docs/INTERVIEW_GUIDE.md](docs/INTERVIEW_GUIDE.md) for the complete LLM selection and evaluation story.

For a file-by-file explanation and demonstration sequence, see [docs/PROJECT_WALKTHROUGH.md](docs/PROJECT_WALKTHROUGH.md). Cloud hardening guidance is in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Security notes

This is portfolio-grade reference code. Before handling real employee data, use an enterprise identity provider, KMS/secret manager, malware scanning, object storage, TLS, row-level security, encrypted backups, retention policies, DLP/PII redaction and an independent security review.

## Resume bullets

- Built **TintinHR**, an authorization-aware agentic HR assistant using FastAPI, Next.js, LangGraph, PostgreSQL/pgvector and Redis, combining policy RAG with employee-specific SQL tools.
- Implemented hybrid vector/BM25 retrieval with reciprocal-rank fusion, CrossEncoder reranking, page-level citations, groundedness checks and safe abstention for unsupported questions.
- Designed role- and department-filtered retrieval, asynchronous document ingestion/versioning, JWT RBAC, audit trails, LLM observability, automated RAG evaluation, Docker and GitHub Actions CI.
