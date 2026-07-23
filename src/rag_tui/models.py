"""Data models for RAG query results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """A retrieved document (or chunk) returned by a RAG pipeline."""

    content: str
    source: str | None = None
    score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RagResult:
    """The outcome of a RAG query: an optional generated answer plus sources."""

    answer: str | None = None
    documents: list[Document] = field(default_factory=list)

    @classmethod
    def coerce(cls, value: RagResult | str | list[Document]) -> RagResult:
        """Normalize the value a pipeline may return into a RagResult."""
        if isinstance(value, RagResult):
            return value
        if isinstance(value, str):
            return cls(answer=value)
        if isinstance(value, list):
            return cls(documents=value)
        raise TypeError(
            f"Pipeline must return RagResult, str, or list[Document], "
            f"got {type(value).__name__}"
        )
