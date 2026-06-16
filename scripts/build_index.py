"""Build or rebuild the Pinecone vector index from the configured dataset."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.rag.pipeline import RAGPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the RAG vector index")
    parser.add_argument("--data-path", default=None, help="Optional dataset path override")
    args = parser.parse_args()

    settings = get_settings()
    pipeline = RAGPipeline(settings)
    data_path = Path(args.data_path) if args.data_path else settings.dataset_path

    count = pipeline.build_index(data_path)
    print(f"Indexed {count} documents into Pinecone index '{settings.pinecone_index_name}'")


if __name__ == "__main__":
    main()
