from proofmap.extract.definitions import extract_definition_edges
from proofmap.model import Node


def definition(id_, title):
    return Node(
        id=id_,
        kind="definition",
        subkind="definition",
        label="定义",
        title=title,
        aliases=[title],
        book_id="b",
        chapter="第1章",
        section="§1",
        pdf_page=1,
        printed_page=1,
        statement="",
        source_chunks=["d1"],
    )


def theorem():
    return Node(
        id="b:定理1.2",
        kind="theorem",
        subkind="theorem",
        label="定理 1.2",
        title="",
        aliases=["定理 1.2"],
        book_id="b",
        chapter="第1章",
        section="§1",
        pdf_page=1,
        printed_page=1,
        statement="",
        source_chunks=["t1"],
    )


def test_term_in_proof_links_to_definition():
    d = definition("b:定义1.1", "一致连续")
    t = theorem()
    edges, issues = extract_definition_edges(
        [d, t], {"b:定理1.2": ("p1", "证明: 由一致连续可得。")}
    )
    assert issues == []
    assert len(edges) == 1
    assert edges[0].type == "definition_term"
    assert edges[0].from_id == "b:定义1.1"
    assert edges[0].to_id == "b:定理1.2"
    assert edges[0].proof_chunk == "p1"
    assert "一致连续" in edges[0].evidence.quote


def test_generic_term_is_ignored():
    d = definition("b:定义1.1", "函数")
    t = theorem()
    edges, _ = extract_definition_edges(
        [d, t], {"b:定理1.2": ("p1", "证明: 由函数可得。")}
    )
    assert edges == []
