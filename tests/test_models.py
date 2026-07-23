import pytest

from rag_tui import Document, RagResult


def test_coerce_passes_through_rag_result():
    result = RagResult(answer="hi")
    assert RagResult.coerce(result) is result


def test_coerce_wraps_str_as_answer():
    result = RagResult.coerce("the answer")
    assert result.answer == "the answer"
    assert result.documents == []


def test_coerce_wraps_document_list():
    docs = [Document(content="chunk")]
    result = RagResult.coerce(docs)
    assert result.answer is None
    assert result.documents == docs


def test_coerce_rejects_other_types():
    with pytest.raises(TypeError, match="got int"):
        RagResult.coerce(42)
