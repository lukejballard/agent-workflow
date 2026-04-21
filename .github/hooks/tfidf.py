"""Lightweight TF-IDF retrieval for the agent hook system.

Uses only the Python standard library. Implements a bag-of-words TF-IDF scorer
for small document collections (< 10,000 entries). The index is built lazily on
first query and cached in memory for the process lifetime.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Any

_INDEX_CACHE: dict[str, tuple[tuple[int, int, tuple[str, ...]], "TFIDFIndex"]] = {}


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [token for token in text.split() if len(token) > 2]


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_stringify(item) for item in value)
    return str(value)


def _doc_text(doc: dict[str, Any], field_keys: list[str] | None) -> str:
    values = [doc.get(key, "") for key in field_keys] if field_keys else doc.values()
    return " ".join(_stringify(value) for value in values)


def _fingerprint(docs: list[dict[str, Any]], field_keys: list[str] | None) -> tuple[int, int, tuple[str, ...]]:
    checksum = 0
    for index, doc in enumerate(docs):
        checksum += (index + 1) * (len(_doc_text(doc, field_keys)) + len(doc))
        stamp = doc.get("ts", doc.get("timestamp", 0))
        if isinstance(stamp, (int, float)):
            checksum += int(float(stamp))
    return len(docs), checksum, tuple(field_keys or ())


class TFIDFIndex:
    """In-memory TF-IDF index over a list of documents."""

    def __init__(
        self,
        docs: list[dict[str, Any]],
        field_keys: list[str] | None = None,
    ) -> None:
        self._docs = docs
        self._field_keys = field_keys
        self._idf: dict[str, float] = {}
        self._doc_vecs: list[dict[str, float]] = []
        self._doc_norms: list[float] = []
        self._build()

    def _build(self) -> None:
        tokenized: list[list[str]] = []
        doc_freq: dict[str, int] = defaultdict(int)
        doc_count = len(self._docs)
        if doc_count == 0:
            return
        for doc in self._docs:
            tokens = _tokenize(_doc_text(doc, self._field_keys))
            tokenized.append(tokens)
            for term in set(tokens):
                doc_freq[term] += 1
        self._idf = {
            term: math.log((doc_count + 1) / (freq + 1)) + 1.0
            for term, freq in doc_freq.items()
        }
        for tokens in tokenized:
            counts = Counter(tokens)
            total = max(len(tokens), 1)
            weights = {
                term: (count / total) * self._idf.get(term, 0.0)
                for term, count in counts.items()
            }
            self._doc_vecs.append(weights)
            self._doc_norms.append(math.sqrt(sum(weight * weight for weight in weights.values())))

    def _query_vector(self, query_tokens: list[str]) -> tuple[dict[str, float], float]:
        counts = Counter(query_tokens)
        total = max(len(query_tokens), 1)
        weights = {
            term: (count / total) * self._idf.get(term, 0.0)
            for term, count in counts.items()
            if term in self._idf
        }
        norm = math.sqrt(sum(weight * weight for weight in weights.values()))
        return weights, norm

    def _score(self, query_vec: dict[str, float], query_norm: float, doc_index: int) -> float:
        doc_norm = self._doc_norms[doc_index]
        if query_norm == 0.0 or doc_norm == 0.0:
            return 0.0
        dot = sum(weight * self._doc_vecs[doc_index].get(term, 0.0) for term, weight in query_vec.items())
        return dot / (query_norm * doc_norm)

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        if not self._docs:
            return []
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []
        query_vec, query_norm = self._query_vector(query_tokens)
        scored = [
            (self._score(query_vec, query_norm, index), index)
            for index in range(len(self._docs))
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [self._docs[index] for score, index in scored[:top_k] if score > 0.0]


def get_cached_index(
    cache_key: str,
    docs: list[dict[str, Any]],
    field_keys: list[str] | None = None,
) -> TFIDFIndex:
    fingerprint = _fingerprint(docs, field_keys)
    cached = _INDEX_CACHE.get(cache_key)
    if cached and cached[0] == fingerprint:
        return cached[1]
    index = TFIDFIndex(docs, field_keys)
    _INDEX_CACHE[cache_key] = (fingerprint, index)
    return index
