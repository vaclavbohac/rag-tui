# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`rag-tui` is a Python library that wraps a user-supplied RAG pipeline in a
[Textual](https://textual.textualize.io/) terminal UI: query prompt at the
bottom, scrolling results pane above it.

## Environment & Commands

- Python 3.11 (pinned in `.python-version`), managed with [uv](https://docs.astral.sh/uv/); hatchling build backend, src layout.
- Run the demo TUI: `uv run main.py`
- Add a dependency: `uv add <package>` (`uv add --dev` for dev tools)
- Run tests: `uv run pytest` (single test: `uv run pytest tests/test_app.py::test_name`)
- Tests are async by default (`asyncio_mode = "auto"`); TUI tests drive the app headlessly with Textual's `app.run_test()` pilot — no terminal needed.
- CI: `.github/workflows/ci.yml` runs pytest on Python 3.11–3.13.

## Domain language & decisions

`CONTEXT.md` defines the canonical terms (**Pipeline**, **Query**, **Document**, **RagResult**) — use them in code and docs; e.g. the plug-in callable is the *pipeline*, never the *handler*. Architectural decisions are recorded in `docs/adr/`.

## Architecture

The library's contract is a single **pipeline** callable (`query: str -> RagResult | str | list[Document]`) that the embedding application supplies; everything else is rendering.

- `src/rag_tui/models.py` — `Document` and `RagResult` dataclasses. `RagResult.coerce()` normalizes the three allowed pipeline return types; extend it if pipelines may return new shapes.
- `src/rag_tui/app.py` — `RagTUI(App)`. Query submission kicks off an exclusive Textual worker: sync pipelines run via `asyncio.to_thread`, async pipelines are awaited, so the UI never blocks. Results (query echo, Markdown answer, one `Collapsible` per document) are appended to the `#results` `VerticalScroll`; pipeline exceptions render inline as an error line rather than crashing the app.
- `main.py` — runnable demo with a fake pipeline; not part of the packaged library.
