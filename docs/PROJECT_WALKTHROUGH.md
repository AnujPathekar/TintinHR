# TintinHR Project Walkthrough

## Repository map

```text
TintinHR/
├── frontend/                 Next.js employee and HR portal
│   ├── app/                  Dashboard, login, chat and document administration
│   ├── components/           Shared shell/navigation/brand components
│   └── lib/                  Auth, typed API client and frontend types
├── backend/
│   ├── app/api/              FastAPI routes and trusted auth dependencies
│   ├── app/core/             Environment configuration and JWT/password security
│   ├── app/db/               Async sessions, demo seeds and sample-document loader
│   ├── app/models/           SQLAlchemy domain/data model
│   ├── app/rag/              Access scope, embeddings, retrieval, LLM and LangGraph agent
│   ├── app/services/         Parsing, ingestion, audit, cache and rate limiting
│   ├── app/workers/          Celery background indexing worker
│   ├── evaluation/           Golden dataset and measurable evaluation runner
│   ├── tests/                Security, routing, chunking and access tests
│   └── alembic/              Versioned PostgreSQL/pgvector schema
├── sample_docs/              Safe fictional policies for demonstration
├── docs/                     Architecture, interview and deployment explanations
├── .github/workflows/        CI checks
└── docker-compose.yml        Full local platform
```

## Request lifecycle

1. `frontend/lib/api.ts` attaches an access token and refreshes it once when required.
2. `backend/app/api/dependencies.py` verifies the JWT, reloads the active user and derives current role/department from PostgreSQL.
3. `backend/app/api/routes/chat.py` rate-limits the user, loads owned history, creates the trusted access scope and checks a scope-partitioned cache.
4. `backend/app/rag/agent.py` rewrites follow-ups and routes to policy retrieval, personal employee data, holiday data or a hybrid path.
5. `backend/app/rag/retrieval.py` applies access/date/version predicates, runs vector and full-text retrieval, fuses ranks and reranks candidates.
6. The LLM receives only authorized context. Its prompt requires evidence markers such as `[1]`.
7. The validator removes invalid citation numbers and refuses policy answers that have no verified citation.
8. The API persists messages and a privacy-conscious audit event, then the portal renders expandable source excerpts.

## Document lifecycle

1. HR/Admin uploads one of PDF, DOCX, TXT or CSV.
2. The API checks extension, size, duplicate SHA-256 and stores an immutable version record.
3. Celery receives the indexing job through Redis.
4. The parser preserves PDF page numbers; the chunker keeps overlap and source metadata.
5. The embedding provider creates normalized vectors, which are written alongside PostgreSQL FTS vectors.
6. A replacement creates version `n+1`; only the current active version is eligible for retrieval.
7. Deletion is a soft archive so it disappears from retrieval without destroying auditability.

## Interview demonstration sequence

1. Log in as Employee and ask: “How many casual leaves do I have left?” This uses SQL only.
2. Ask: “Can I carry them forward?” This demonstrates memory/query rewriting and policy RAG.
3. Ask: “Based on my balance and policy, what should I use before year end?” This demonstrates hybrid structured/unstructured reasoning.
4. Upload an HR-only policy, ask for it as Employee, and show that it cannot be retrieved; log in as HR and repeat.
5. Replace the Leave Policy and show the processing → active version transition.
6. Run the golden evaluation and show retrieval, citation, abstention, groundedness, latency and token metrics.

## Honest scope statement

The repository is a complete portfolio implementation and local runnable reference. For real HR production data, follow `DEPLOYMENT.md`: enterprise SSO, object storage, malware scanning, KMS, private networking, RLS, retention/DLP, encrypted backups and an independent security review are required.
