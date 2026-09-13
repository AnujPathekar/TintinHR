import asyncio
import math
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.rag.access import AccessScope
from app.rag.embeddings import get_embedding_service


@dataclass
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    title: str
    filename: str
    page_number: int | None
    content: str
    score: float


HYBRID_SQL = text("""
WITH eligible AS (
  SELECT c.*, d.title, d.filename
  FROM document_chunks c
  JOIN documents d ON d.id = c.document_id
  WHERE d.status = 'ACTIVE'::document_status
    AND c.version = d.current_version
    AND d.visibility = ANY(CAST(:visibilities AS document_visibility[]))
    AND (d.department_id IS NULL OR d.department_id = :department_id)
    AND (d.valid_from IS NULL OR d.valid_from <= CURRENT_DATE)
    AND (d.valid_until IS NULL OR d.valid_until >= CURRENT_DATE)
), vector_hits AS (
  SELECT *, row_number() OVER (ORDER BY embedding <=> CAST(:embedding AS vector)) AS rank
  FROM eligible ORDER BY embedding <=> CAST(:embedding AS vector) LIMIT :vector_k
), keyword_hits AS (
  SELECT *, row_number() OVER (ORDER BY ts_rank_cd(search_vector, plainto_tsquery('english', :query)) DESC) AS rank
  FROM eligible
  WHERE search_vector @@ plainto_tsquery('english', :query)
  ORDER BY ts_rank_cd(search_vector, plainto_tsquery('english', :query)) DESC LIMIT :keyword_k
), fused AS (
  SELECT id, SUM(score) AS score FROM (
    SELECT id, 1.0 / (60 + rank) AS score FROM vector_hits
    UNION ALL
    SELECT id, 1.0 / (60 + rank) AS score FROM keyword_hits
  ) ranks GROUP BY id
)
SELECT e.id, e.document_id, e.title, e.filename, e.page_number, e.content, f.score
FROM fused f JOIN eligible e ON e.id = f.id
ORDER BY f.score DESC LIMIT :candidate_limit
""")


class HybridRetriever:
    def __init__(self) -> None:
        self._reranker = None

    async def retrieve(self, db: AsyncSession, query: str, scope: AccessScope) -> list[RetrievedChunk]:
        embedding = await get_embedding_service().embed_query(query)
        result = await db.execute(
            HYBRID_SQL,
            {
                "visibilities": [v.name for v in scope.visibilities],
                "department_id": scope.department_id,
                "embedding": "[" + ",".join(map(str, embedding)) + "]",
                "query": query,
                "vector_k": settings.vector_top_k,
                "keyword_k": settings.keyword_top_k,
                "candidate_limit": max(settings.final_top_k * 3, 12),
            },
        )
        chunks = [RetrievedChunk(*row) for row in result.all()]
        if settings.enable_reranker and len(chunks) > 1:
            chunks = await self._rerank(query, chunks)
        return chunks[: settings.final_top_k]

    async def _rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if self._reranker is None:
            from sentence_transformers import CrossEncoder

            self._reranker = CrossEncoder(settings.reranker_model)
        scores = await asyncio.to_thread(
            self._reranker.predict, [(query, chunk.content) for chunk in chunks]
        )
        reranked = []
        for chunk, score in zip(chunks, scores, strict=True):
            probability = 1 / (1 + math.exp(-float(score)))
            if probability >= settings.min_retrieval_score:
                reranked.append(RetrievedChunk(**{**chunk.__dict__, "score": probability}))
        return sorted(reranked, key=lambda item: item.score, reverse=True)
