from __future__ import annotations

import hashlib
import math
import re
from typing import Sequence

from langchain_core.embeddings import Embeddings


class HashEmbeddings(Embeddings):
    """Lightweight deterministic embeddings for local dev and CI without GPU/RAM-heavy models."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        if not tokens:
            tokens = ["empty"]

        vector = [0.0] * self.dimensions
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for index in range(self.dimensions):
                vector[index] += digest[index % len(digest)] / 255.0

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)
