from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings


@lru_cache
def get_chat_model() -> BaseChatModel:
    provider = settings.llm_provider.lower()
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.llm_model, google_api_key=settings.llm_api_key, temperature=0
        )

    from langchain_openai import ChatOpenAI

    kwargs = {"model": settings.llm_model, "temperature": 0}
    if provider == "groq":
        kwargs.update(api_key=settings.llm_api_key, base_url="https://api.groq.com/openai/v1")
    elif provider == "ollama":
        kwargs.update(api_key="ollama", base_url=settings.llm_base_url)
    else:
        kwargs.update(api_key=settings.llm_api_key)
        if settings.llm_base_url and provider not in {"openai"}:
            kwargs["base_url"] = settings.llm_base_url
    return ChatOpenAI(**kwargs)

