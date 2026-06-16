import json
from pathlib import Path

import pandas as pd


def _record_to_text(row: dict) -> str:
    title = str(row.get("title", "")).strip()
    question = str(row.get("question", row.get("body", ""))).strip()
    answer = str(row.get("answer", row.get("accepted_answer", ""))).strip()
    tags = row.get("tags", "")
    if isinstance(tags, list):
        tags = ", ".join(tags)
    tags = str(tags).strip()

    parts = [f"Title: {title}" if title else "", f"Question: {question}" if question else ""]
    if tags:
        parts.append(f"Tags: {tags}")
    if answer:
        parts.append(f"Answer: {answer}")
    return "\n".join(part for part in parts if part)


def load_qa_records(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path}")

    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
        raise ValueError("JSON dataset must be a list of records")

    if suffix == ".csv":
        frame = pd.read_csv(path)
        return frame.to_dict(orient="records")

    raise ValueError(f"Unsupported dataset format: {suffix}")


def prepare_documents(records: list[dict]) -> tuple[list[str], list[dict], list[str]]:
    texts: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for index, record in enumerate(records):
        text = _record_to_text(record)
        if not text.strip():
            continue
        doc_id = str(record.get("id", index))
        title = str(record.get("title", f"Python Q&A #{doc_id}"))
        texts.append(text)
        metadatas.append({"title": title, "source_id": doc_id})
        ids.append(doc_id)

    return texts, metadatas, ids
