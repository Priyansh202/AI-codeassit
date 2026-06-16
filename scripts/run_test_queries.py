"""Run manual API evaluation queries and capture responses."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.main import app
from app.rag.pipeline import RAGPipeline

TEST_QUERIES = [
    "How do I read a CSV file in pandas?",
    "What is the difference between a list and a tuple?",
    "How can I handle missing values in a DataFrame?",
    "Explain Python list comprehensions with an example.",
    "How do I merge two DataFrames on a common key?",
    "What does if __name__ == '__main__' do?",
    "How do I create and use a virtual environment?",
    "How do I train-test split data with scikit-learn?",
    "How do I sort a list in Python?",
    "What is a decorator in Python?",
]


def main() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    pipeline = RAGPipeline(settings)
    pipeline.build_index(settings.dataset_path)

    import app.main as main_module

    main_module.pipeline = pipeline

    results: list[dict] = []
    with TestClient(app) as client:
        for question in TEST_QUERIES:
            response = client.post("/ask", json={"question": question})
            payload = response.json()
            results.append(
                {
                    "question": question,
                    "status_code": response.status_code,
                    "mode": payload.get("mode"),
                    "answer": payload.get("answer"),
                    "top_source": payload.get("sources", [{}])[0],
                    "observation": _observation(question, payload),
                }
            )

    output = {
        "generated_at": datetime.now(UTC).isoformat(),
        "llm_configured": settings.has_llm_credentials(),
        "document_count": pipeline.document_count,
        "results": results,
    }

    out_path = ROOT / "test_results" / "api_test_results.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


def _observation(question: str, payload: dict) -> str:
    answer = (payload.get("answer") or "").lower()
    if payload.get("mode") == "retrieval_only":
        return "Retrieval-only mode (no LLM key). Answer grounded in top Stack Overflow match."
    if "kubernetes" in question.lower():
        return "Out-of-domain query; system should avoid hallucinating infra details."
    if any(token in answer for token in ["pandas", "list", "tuple", "python", "dataframe", "sklearn"]):
        return "Answer appears grounded in Python/data-science context."
    return "Review manually for completeness."


if __name__ == "__main__":
    main()
