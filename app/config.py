from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: str = "openrouter"
    openai_api_key: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    groq_model: str = "llama-3.3-70b-versatile"
    openrouter_model: str = "liquid/lfm-2.5-1.2b-instruct:free"
    openrouter_site_url: str = "http://localhost:8000"
    openrouter_app_name: str = "Python Q&A Assistant"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_provider: str = "auto"
    embedding_dimension: int = 384
    top_k: int = 5
    pinecone_api_key: str = ""
    pinecone_index_name: str = "python-qa-assistant"
    pinecone_namespace: str = "default"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    data_path: str = "./data/sample_python_qa.json"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @property
    def dataset_path(self) -> Path:
        return Path(self.data_path)

    def has_pinecone_credentials(self) -> bool:
        return bool(self.pinecone_api_key)

    def has_llm_credentials(self) -> bool:
        if self.llm_provider == "groq":
            return bool(self.groq_api_key)
        if self.llm_provider == "openrouter":
            return bool(self.openrouter_api_key)
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
