# rag-tui

A library that wraps a developer's RAG pipeline in a terminal UI. The primary
user is a **RAG developer** using the TUI as an inspection instrument while
building and tuning a pipeline — retrieval scores, sources, and retrieved
content are first-class, not debug clutter. It is not an end-user chat
front-end.

## Language

**Document**:
A retrieved unit of context returned by the pipeline — may be a whole file or a chunk of one.
_Avoid_: Chunk, passage, hit

**Badge**:
A short label the Pipeline attaches to a Document for display in its panel title ("negative", "faq").
_Avoid_: Tag, label, annotation

**Pipeline**:
The developer's own RAG system — retrieval plus optional generation — supplied to the TUI as a callable (`query -> RagResult`).
_Avoid_: Handler, backend, engine

**Query**:
A single question the developer submits to the Pipeline from the prompt.
_Avoid_: Prompt (that's the input widget), message

**RagResult**:
The Pipeline's response to one Query: an optional generated answer plus the retrieved Documents.
_Avoid_: Response, output

**Report**:
A short note the Pipeline emits through its optional second-argument callback while a Query runs ("reranking 20 candidates…").
_Avoid_: Status, progress message, log line

**Trace**:
The persisted sequence of a Query's Reports with per-stage elapsed times, kept in the transcript above the RagResult.
_Avoid_: History, timeline

## Relationships

- A **Query** is answered by exactly one **RagResult**
- A **RagResult** contains zero or more **Documents** and at most one answer
- One **Query** runs at a time — the prompt locks while the **Pipeline** runs
  (deliberate: no abort, no overlapping queries, until practice shows it hurts)
- A **Pipeline** may emit zero or more **Reports** per **Query**; each Report
  starts a stage whose elapsed time runs until the next Report (or completion)
- A **Query** gains a **Trace** only if its Pipeline emitted Reports —
  one-argument Pipelines produce no Trace and keep working unchanged
- A **Document** carries zero or more **Badges**; its `metadata` is opaque to
  the TUI — never rendered, never interpreted (ADR 0003)

## Example dialogue

> **Dev:** "When a **Query** is submitted, does the TUI call my **Pipeline**
> once for retrieval and once for generation?"
> **Domain expert:** "No — the TUI knows nothing about your Pipeline's
> internals. It calls it exactly once per Query and gets back one
> **RagResult**; whether that contains an answer, **Documents**, or both is
> the Pipeline's business."
> **Dev:** "And if my Pipeline is retrieval-only?"
> **Domain expert:** "Return just the Documents — a RagResult with no answer
> is a perfectly good result."

## Flagged ambiguities

- "TUI for writing RAG systems" could have meant an end-user chat UI —
  resolved: the audience is the developer of the pipeline, which is why
  scores and source paths are displayed prominently.
- The plug-in callable was originally named "handler" — resolved: it is the
  **Pipeline**; the code was renamed (`RagTUI(pipeline=...)`) so the API
  speaks the domain language.
- The project directory was named "rag-cli-skeleton" while the distribution
  was "rag-tui" — resolved: renamed the directory to `rag-tui`; one name
  everywhere (directory, distribution, package, CI).
- Rendering `metadata["badge"]` was proposed to give metadata a visible role —
  resolved: display-worthy attributes get first-class fields (**Badge**);
  metadata stays an opaque bag the TUI never reads.
