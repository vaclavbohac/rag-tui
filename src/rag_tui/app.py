"""The Textual application that renders the RAG query TUI."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from typing import Union

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Collapsible, Footer, Header, Input, Markdown

from .models import Document, RagResult

PipelineResult = Union[RagResult, str, "list[Document]"]
Pipeline = Callable[[str], Union[PipelineResult, Awaitable[PipelineResult]]]


class RagTUI(App):
    """A terminal UI for interactively querying a RAG pipeline.

    Pass a pipeline that takes the query string and returns a ``RagResult``
    (or a plain answer string, or a list of ``Document``). The pipeline may
    be sync (it runs in a worker thread) or async.

        app = RagTUI(pipeline=my_rag_pipeline)
        app.run()
    """

    TITLE = "RAG TUI"

    CSS = """
    #results {
        padding: 0 1;
    }
    .query-echo {
        margin-top: 1;
    }
    Collapsible {
        margin-left: 2;
    }
    """

    BINDINGS = [("ctrl+l", "clear_results", "Clear results")]

    def __init__(self, pipeline: Pipeline, *, title: str | None = None) -> None:
        super().__init__()
        self.pipeline = pipeline
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
        try:
            result = await self._call_pipeline(query)
        except Exception as error:
            await status.update(f"**Error:** {error}")
        else:
            await status.remove()
            for widget in self._render_result(result):
                await results.mount(widget)
        finally:
            query_input.disabled = False
            query_input.focus()
            results.scroll_end(animate=False)

    async def _call_pipeline(self, query: str) -> RagResult:
        if inspect.iscoroutinefunction(self.pipeline):
            value = await self.pipeline(query)
        else:
            value = await asyncio.to_thread(self.pipeline, query)
            if inspect.isawaitable(value):
                value = await value
        return RagResult.coerce(value)

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
