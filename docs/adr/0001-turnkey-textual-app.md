# rag-tui is a turnkey Textual app, not a widget library

The developer supplies a single Pipeline callable (`query -> RagResult`) and
rag-tui owns the entire [Textual](https://textual.textualize.io/) `App` —
layout, input handling, worker scheduling, and rendering. The alternative was
shipping embeddable widgets (a results pane, a query prompt) for developers to
compose into their own Textual apps. We chose the turnkey shape because the
target user is a RAG developer who wants an inspection instrument with zero UI
work, not a TUI author; a widget-level API can still be extracted later, while
the reverse (retrofitting a stable turnkey API onto widgets) breaks users.
This also commits the library to Textual: `RagTUI` subclasses `textual.App`,
so the framework is part of the public API, not an implementation detail.
