import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

os.environ.setdefault("DATA_PATH", str(ROOT / "data" / "sample_python_qa.json"))
os.environ.setdefault("EMBEDDING_PROVIDER", "hash")
os.environ.setdefault("PINECONE_NAMESPACE", "pytest")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("GROQ_API_KEY", "")


@pytest.fixture(scope="session")
def client() -> TestClient:
    from app.config import get_settings
    from app.main import app
    from app.rag.pipeline import RAGPipeline
    from app.rag.vectorstore import clear_namespace

    get_settings.cache_clear()
    settings = get_settings()

    if not settings.has_pinecone_credentials():
        pytest.skip("PINECONE_API_KEY is not configured")

    pipeline = RAGPipeline(settings)
    pipeline.build_index(settings.dataset_path)

    import app.main as main_module

    main_module.pipeline = pipeline
    main_module.settings = settings

    with TestClient(app) as test_client:
        yield test_client

    clear_namespace(settings)
