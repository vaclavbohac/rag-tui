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
- `Document.badges` — short labels like `["negative", "faq"]` — render in the
  panel title: `#general · score 0.910 · negative`. `Document.metadata` is
  never rendered; it's opaque storage for your own bookkeeping.
- `Ctrl+L` clears the results pane.

## Progress reporting

Multi-stage pipelines (route → rerank → answer) can take 10+ seconds. If your
pipeline accepts a second positional parameter, it receives a `report`
callback:

```python
def my_pipeline(query: str, report) -> RagResult:
    report("routing query…")
    route = pick_route(query)
    report("reranking 20 candidates…")
    docs = rerank(retrieve(query))
    report("writing answer…")
    return RagResult(answer=generate(query, docs), documents=docs)
```

While the query runs, the status line shows the latest report. When the
result arrives, the reports persist as a per-stage timing trace above it:

```
routing query… 0.8s · reranking 20 candidates… 6.1s · writing answer… 3.2s
```

One-argument pipelines work unchanged and produce no trace. The trace is also
kept when the pipeline raises mid-stage, so you can see how far it got.

## Demo

```sh
uv run main.py
```

Runs the TUI against a fake pipeline in `main.py` — a template for wiring in
your own.
