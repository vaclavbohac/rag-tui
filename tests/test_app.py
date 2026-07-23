import asyncio

from textual.widgets import Collapsible, Input, Markdown

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
