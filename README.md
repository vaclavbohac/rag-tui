# rag-tui

A Python library that gives your RAG pipeline a terminal UI: a prompt where the
user types a query, presses Enter, and sees the generated answer plus the
retrieved source documents.

Built on [Textual](https://textual.textualize.io/).

## Usage

Write a pipeline that takes the query string and returns a result, then hand it
to `RagTUI`:

```python
from rag_tui import Document, RagResult, RagTUI

def my_pipeline(query: str) -> RagResult:
    docs = retrieve(query)          # your retriever
    answer = generate(query, docs)  # your generator
    return RagResult(
        answer=answer,
        documents=[Document(content=d.text, source=d.path, score=d.score) for d in docs],
    )

RagTUI(my_pipeline, title="My RAG app").run()
```

- The pipeline may be **sync** (runs in a worker thread so the UI stays
  responsive) or **async**.
- It may return a `RagResult`, a plain `str` (treated as the answer), or a
  `list[Document]` (retrieval-only, no answer).
- Answers render as Markdown; each document appears as a collapsible panel
  with its source and score.
- `Ctrl+L` clears the results pane.

## Demo

```sh
uv run main.py
```

Runs the TUI against a fake pipeline in `main.py` — a template for wiring in
your own.
