import asyncio
from functools import lru_cache

from app.core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self._model = None

    def _sentence_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(settings.embedding_model)
        return self._model

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if settings.embedding_provider == "openai":
            from langchain_openai import OpenAIEmbeddings

            model = OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.llm_api_key)
            return await model.aembed_documents(texts)
        model = self._sentence_model()
        vectors = await asyncio.to_thread(model.encode, texts, normalize_embeddings=True)
        return vectors.tolist()

    async def embed_query(self, text: str) -> list[float]:
        return (await self.embed_documents([text]))[0]


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()

