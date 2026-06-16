from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from pinecone.exceptions import NotFoundException

from app.config import Settings


def embedding_dimension(embeddings: Embeddings, settings: Settings) -> int:
    if settings.embedding_dimension:
        return settings.embedding_dimension
    if hasattr(embeddings, "dimensions"):
        return int(embeddings.dimensions)
    return len(embeddings.embed_query("dimension-probe"))


def _pinecone_client(settings: Settings) -> Pinecone:
    if not settings.pinecone_api_key:
        raise ValueError("PINECONE_API_KEY is not configured")
    return Pinecone(api_key=settings.pinecone_api_key)


def ensure_pinecone_index(settings: Settings, dimension: int):
    client = _pinecone_client(settings)
    existing = {index.name for index in client.list_indexes()}
    if settings.pinecone_index_name not in existing:
        client.create_index(
            name=settings.pinecone_index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
        )
    return client.Index(settings.pinecone_index_name)


def connect_vectorstore(settings: Settings, embeddings: Embeddings) -> PineconeVectorStore:
    dimension = embedding_dimension(embeddings, settings)
    index = ensure_pinecone_index(settings, dimension)
    return PineconeVectorStore(
        index=index,
        embedding=embeddings,
        namespace=settings.pinecone_namespace,
    )


def _index_stats(settings: Settings):
    client = _pinecone_client(settings)
    if settings.pinecone_index_name not in {index.name for index in client.list_indexes()}:
        return None
    index = client.Index(settings.pinecone_index_name)
    return index.describe_index_stats()


def _namespace_vector_count(stats, namespace: str) -> int:
    if not stats:
        return 0

    namespaces = getattr(stats, "namespaces", None) or stats.get("namespaces", {})
    if namespace:
        namespace_stats = namespaces.get(namespace, {})
        if hasattr(namespace_stats, "vector_count"):
            return int(namespace_stats.vector_count)
        return int(namespace_stats.get("vector_count", 0))

    total = getattr(stats, "total_vector_count", None)
    if total is not None:
        return int(total)
    return int(stats.get("total_vector_count", 0))


def vector_count(settings: Settings) -> int:
    stats = _index_stats(settings)
    return _namespace_vector_count(stats, settings.pinecone_namespace)


def clear_namespace(settings: Settings) -> None:
    stats = _index_stats(settings)
    if _namespace_vector_count(stats, settings.pinecone_namespace) == 0:
        return

    client = _pinecone_client(settings)
    index = client.Index(settings.pinecone_index_name)
    try:
        index.delete(delete_all=True, namespace=settings.pinecone_namespace)
    except NotFoundException:
        return
