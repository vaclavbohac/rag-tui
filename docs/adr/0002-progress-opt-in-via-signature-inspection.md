# Progress opt-in via signature inspection

A Pipeline opts into progress reporting by accepting a second positional
parameter — `def ask(query, report)` — which the TUI detects by attempting a
two-argument signature bind and, on success, fills with a `report` callback.
One-argument Pipelines keep working unchanged.

## Considered Options

- **Context function** (`rag_tui.report(...)` wired via contextvars): callable
  at any depth without plumbing, but too magical and silently a no-op when the
  Pipeline runs outside the TUI.
- **Generator Pipelines** (yield Reports, return the RagResult): a natural
  path to token streaming, but it reshapes the entire Pipeline contract and is
  the most invasive change for existing code.

## Consequences

Callables without an inspectable two-positional-argument signature (e.g.
`**kwargs`-only wrappers) are treated as one-argument Pipelines; to receive
Reports they must expose a real second positional parameter.
