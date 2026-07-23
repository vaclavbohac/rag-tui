"""The Textual application that renders the RAG query TUI."""

from __future__ import annotations

import asyncio
import inspect
import time
from collections.abc import Awaitable, Callable
from typing import Union

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Collapsible, Footer, Header, Input, Markdown, Static

from .models import Document, RagResult

Report = Callable[[str], None]
PipelineResult = Union[RagResult, str, "list[Document]"]
Pipeline = Union[
    Callable[[str], Union[PipelineResult, Awaitable[PipelineResult]]],
    Callable[[str, Report], Union[PipelineResult, Awaitable[PipelineResult]]],
]


def _accepts_report(pipeline: Pipeline) -> bool:
    """True if the pipeline can take a report callback as a second positional arg."""
    try:
        signature = inspect.signature(pipeline)
    except (TypeError, ValueError):
        return False
    try:
        signature.bind("query", lambda message: None)
    except TypeError:
        return False
    return True


class RagTUI(App):
    """A terminal UI for interactively querying a RAG pipeline.

    Pass a pipeline that takes the query string and returns a ``RagResult``
    (or a plain answer string, or a list of ``Document``). The pipeline may
    be sync (it runs in a worker thread) or async.

        app = RagTUI(pipeline=my_rag_pipeline)
        app.run()

    A pipeline that accepts a second positional parameter receives a
    ``report`` callback for progress updates::

        def ask(query: str, report: Report) -> RagResult:
            report("reranking 20 candidates…")
            ...

    Reports update the status line while the query runs and persist as a
    per-stage timing trace above the result.
    """

    TITLE = "RAG TUI"

    CSS = """
    #results {
        padding: 0 1;
    }
    .query-echo {
        margin-top: 1;
    }
    .trace {
        color: $text-muted;
    }
    Collapsible {
        margin-left: 2;
    }
    """

    BINDINGS = [("ctrl+l", "clear_results", "Clear results")]

    def __init__(self, pipeline: Pipeline, *, title: str | None = None) -> None:
        super().__init__()
        self.pipeline = pipeline
        self._sends_reports = _accepts_report(pipeline)
        if title is not None:
            self.title = title

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(id="results")
        yield Input(placeholder="Enter your query and press Enter…", id="query")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#query", Input).focus()

    def action_clear_results(self) -> None:
        self.query_one("#results", VerticalScroll).remove_children()

    @on(Input.Submitted, "#query")
    def _on_query_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        event.input.clear()
        self._run_query(query)

    @work(exclusive=True)
    async def _run_query(self, query: str) -> None:
        results = self.query_one("#results", VerticalScroll)
        query_input = self.query_one("#query", Input)
        query_input.disabled = True
        await results.mount(Markdown(f"**❯ {query}**", classes="query-echo"))
        status = Markdown("*Running query…*")
        await results.mount(status)
        results.scroll_end(animate=False)

        reports: list[tuple[str, float]] = []

        def record_report(message: str) -> None:
            reports.append((str(message), time.monotonic()))
            status.update(f"*{message}*")
            results.scroll_end(animate=False)

        def report(message: str) -> None:
            # Sync pipelines call this from the worker thread; async ones
            # call it on the UI thread, where call_from_thread raises.
            try:
                self.call_from_thread(record_report, message)
            except RuntimeError:
                record_report(message)

        try:
            result = await self._call_pipeline(query, report)
        except Exception as error:
            await self._mount_trace(results, reports, before=status)
            await status.update(f"**Error:** {error}")
        else:
            await status.remove()
            await self._mount_trace(results, reports)
            for widget in self._render_result(result):
                await results.mount(widget)
        finally:
            query_input.disabled = False
            query_input.focus()
            results.scroll_end(animate=False)

    async def _call_pipeline(self, query: str, report: Report) -> RagResult:
        args = (query, report) if self._sends_reports else (query,)
        if inspect.iscoroutinefunction(self.pipeline):
            value = await self.pipeline(*args)
        else:
            value = await asyncio.to_thread(self.pipeline, *args)
            if inspect.isawaitable(value):
                value = await value
        return RagResult.coerce(value)

    async def _mount_trace(
        self,
        results: VerticalScroll,
        reports: list[tuple[str, float]],
        *,
        before: Widget | None = None,
    ) -> None:
        """Persist the query's reports as one line with per-stage elapsed times."""
        if not reports:
            return
        stage_ends = [timestamp for _, timestamp in reports[1:]] + [time.monotonic()]
        parts = [
            f"{message} {end - started:.1f}s"
            for (message, started), end in zip(reports, stage_ends)
        ]
        trace = Static(" · ".join(parts), classes="trace")
        if before is not None:
            await results.mount(trace, before=before)
        else:
            await results.mount(trace)

    def _render_result(self, result: RagResult) -> list[Widget]:
        widgets: list[Widget] = []
        if result.answer:
            widgets.append(Markdown(result.answer))
        for index, doc in enumerate(result.documents, start=1):
            title = doc.source or f"Document {index}"
            if doc.score is not None:
                title = f"{title}  ·  score {doc.score:.3f}"
            widgets.append(Collapsible(Markdown(doc.content), title=title))
        if not widgets:
            widgets.append(Markdown("*No results.*"))
        return widgets
