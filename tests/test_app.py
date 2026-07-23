import asyncio
import re

from textual.widgets import Collapsible, Input, Markdown, Static

from rag_tui import Document, RagResult, RagTUI


async def submit_query(app: RagTUI, pilot, query: str) -> None:
    """Type a query, press Enter, and wait for the pipeline worker to finish."""
    await pilot.press(*query, "enter")
    for _ in range(100):
        await pilot.pause(0.05)
        if not app.query_one("#query", Input).disabled:
            return
    raise AssertionError("query worker did not finish in time")


def markdown_sources(app: RagTUI) -> list[str]:
    return [widget.source for widget in app.query(Markdown)]


async def test_sync_pipeline_renders_answer_and_documents():
    def pipeline(query: str) -> RagResult:
        return RagResult(
            answer=f"answer to {query}",
            documents=[Document(content="chunk text", source="doc.md", score=0.9)],
        )

    app = RagTUI(pipeline)
    async with app.run_test() as pilot:
        await submit_query(app, pilot, "hello")

        sources = markdown_sources(app)
        assert "**❯ hello**" in sources
        assert "answer to hello" in sources
        assert "chunk text" in sources

        (collapsible,) = app.query(Collapsible)
        assert collapsible.title == "doc.md  ·  score 0.900"


async def test_async_pipeline_with_plain_string_result():
    async def pipeline(query: str) -> str:
        await asyncio.sleep(0.01)
        return f"async answer to {query}"

    app = RagTUI(pipeline)
    async with app.run_test() as pilot:
        await submit_query(app, pilot, "hi")
        assert "async answer to hi" in markdown_sources(app)


async def test_document_list_result_renders_collapsibles_only():
    def pipeline(query: str) -> list[Document]:
        return [Document(content="first"), Document(content="second")]

    app = RagTUI(pipeline)
    async with app.run_test() as pilot:
        await submit_query(app, pilot, "docs only")

        collapsibles = list(app.query(Collapsible))
        assert [c.title for c in collapsibles] == ["Document 1", "Document 2"]


async def test_pipeline_error_is_shown_inline():
    def pipeline(query: str) -> RagResult:
        raise RuntimeError("pipeline exploded")

    app = RagTUI(pipeline)
    async with app.run_test() as pilot:
        await submit_query(app, pilot, "boom")

        assert "**Error:** pipeline exploded" in markdown_sources(app)
        assert not app.query_one("#query", Input).disabled


async def test_empty_result_shows_placeholder():
    app = RagTUI(lambda query: RagResult())
    async with app.run_test() as pilot:
        await submit_query(app, pilot, "nothing")
        assert "*No results.*" in markdown_sources(app)


async def test_blank_query_is_ignored():
    calls: list[str] = []

    def pipeline(query: str) -> str:
        calls.append(query)
        return "should not happen"

    app = RagTUI(pipeline)
    async with app.run_test() as pilot:
        await pilot.press("space", "enter")
        await pilot.pause(0.1)
        assert calls == []
        assert len(app.query(Markdown)) == 0


async def test_input_is_cleared_and_refocused_after_query():
    app = RagTUI(lambda query: "done")
    async with app.run_test() as pilot:
        await submit_query(app, pilot, "hello")
        query_input = app.query_one("#query", Input)
        assert query_input.value == ""
        assert app.focused is query_input


async def test_ctrl_l_clears_results():
    app = RagTUI(lambda query: "done")
    async with app.run_test() as pilot:
        await submit_query(app, pilot, "hello")
        assert len(app.query(Markdown)) > 0

        await pilot.press("ctrl+l")
        await pilot.pause()
        assert len(app.query(Markdown)) == 0


def trace_text(app: RagTUI) -> str:
    (trace,) = app.query(".trace").results(Static)
    return str(trace.content)


async def test_two_arg_pipeline_gets_report_and_trace_persists():
    def pipeline(query: str, report) -> str:
        report("routing…")
        report("reranking 20 candidates…")
        return "done"

    app = RagTUI(pipeline)
    async with app.run_test() as pilot:
        await submit_query(app, pilot, "q")

        text = trace_text(app)
        assert re.fullmatch(
            r"routing… \d+\.\ds · reranking 20 candidates… \d+\.\ds", text
        ), text
        assert "done" in markdown_sources(app)


async def test_report_updates_status_line_live():
    gate = asyncio.Event()

    async def pipeline(query: str, report) -> str:
        report("stage one…")
        await gate.wait()
        return "done"

    app = RagTUI(pipeline)
    async with app.run_test() as pilot:
        await pilot.press("q", "enter")
        for _ in range(100):
            await pilot.pause(0.02)
            if "*stage one…*" in markdown_sources(app):
                break
        else:
            raise AssertionError("status line never showed the report")
        gate.set()
        await submit_query(app, pilot, "")  # just waits for completion
        assert "*stage one…*" not in markdown_sources(app)


async def test_trace_persists_when_pipeline_errors_mid_stage():
    def pipeline(query: str, report) -> str:
        report("routing…")
        raise RuntimeError("boom")

    app = RagTUI(pipeline)
    async with app.run_test() as pilot:
        await submit_query(app, pilot, "q")
        assert "routing…" in trace_text(app)
        assert "**Error:** boom" in markdown_sources(app)


async def test_pipeline_with_optional_report_param_receives_callback():
    received = []

    def pipeline(query: str, report=None) -> str:
        received.append(report)
        return "ok"

    app = RagTUI(pipeline)
    async with app.run_test() as pilot:
        await submit_query(app, pilot, "q")
        assert received[0] is not None


async def test_one_arg_pipeline_produces_no_trace():
    app = RagTUI(lambda query: "done")
    async with app.run_test() as pilot:
        await submit_query(app, pilot, "q")
        assert len(app.query(".trace")) == 0
