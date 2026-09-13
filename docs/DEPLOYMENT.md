# Deployment Guide

## Local

Use Docker Compose as described in the README. Keep Ollama on the host or configure a cloud LLM.

## Cloud reference architecture

- Next.js: Vercel or a container service.
- FastAPI and Celery: AWS ECS/Fargate, Azure Container Apps or Kubernetes.
- PostgreSQL + pgvector: RDS PostgreSQL/Aurora, Azure Database for PostgreSQL or a managed pgvector provider.
- Redis: ElastiCache or Azure Cache for Redis.
- Files: private S3/Blob Storage with short-lived signed downloads; replace the local filesystem adapter.
- Secrets: AWS Secrets Manager/Azure Key Vault; never ship `.env`.
- Identity: OIDC/SAML through the company's IdP; map group claims to server-side roles.

## Production checklist

1. Terminate TLS at a managed load balancer and enforce HTTPS/HSTS.
2. Replace demo password auth/localStorage with OIDC and secure, HttpOnly, SameSite cookies.
3. Use KMS-backed encryption, private networking, restricted security groups and encrypted backups.
4. Scan uploads for malware and archive originals in private object storage.
5. Add PostgreSQL row-level security as defense in depth for employee and document scopes.
6. Redact PII from logs/traces; configure data retention and model-provider zero-retention terms.
7. Run migrations as a one-off release job, then deploy API and workers with rolling health checks.
8. Export OpenTelemetry metrics/logs/traces; alert on indexing failures, denial spikes, p95 latency and evaluation regressions.
9. Run restore drills, load tests, prompt-injection tests and access-leakage tests before launch.

