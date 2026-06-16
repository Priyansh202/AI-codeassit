from __future__ import annotations

from langchain_core.embeddings import Embeddings

from app.config import Settings
from app.rag.embeddings import HashEmbeddings


def create_embeddings(settings: Settings) -> Embeddings:
    provider = settings.embedding_provider.lower()

    if provider == "auto":
        if settings.openai_api_key:
            provider = "openai"
        else:
            provider = "hash"

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model="text-embedding-3-small",
        )

    if provider == "huggingface":
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(model_name=settings.embedding_model)

    if provider == "hash":
        return HashEmbeddings()

    raise ValueError(f"Unsupported embedding provider: {provider}")
