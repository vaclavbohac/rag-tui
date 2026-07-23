"""Demo of the rag-tui library with a fake RAG pipeline."""

import time

from rag_tui import Document, RagResult, RagTUI


def demo_pipeline(query: str) -> RagResult:
    """Stand-in for a real RAG pipeline: retrieve documents, generate an answer."""
    time.sleep(0.5)  # simulate retrieval + generation latency
    return RagResult(
        answer=f"This is a placeholder answer for: *{query}*\n\n"
        "Replace `demo_pipeline` with your own retrieval + generation pipeline.",
        documents=[
            Document(
                content="Retrieval-augmented generation combines a retriever "
                "with a generator to ground answers in source documents.",
                source="docs/rag-overview.md",
                score=0.92,
            ),
            Document(
                content="Chunking strategy has a large impact on retrieval "
                "quality; overlapping windows are a common default.",
                source="docs/chunking.md",
                score=0.87,
            ),
        ],
    )


def main() -> None:
    RagTUI(demo_pipeline, title="RAG TUI demo").run()


if __name__ == "__main__":
    main()
