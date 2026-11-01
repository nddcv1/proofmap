from proofmap.extract.anaphora import extract_anaphora_edges
from proofmap.extract.named import extract_named_edges
from proofmap.extract.numbered import extract_numbered_edges
from proofmap.model import Node
from proofmap.resolve import NodeIndex


def node(id_, label, chapter="第1章", aliases=None, source_chunks=None):
    return Node(
        id=id_,
        kind="theorem",
        subkind="theorem",
        label=label,
        title=label,
        aliases=aliases or [label],
        book_id="b",
        chapter=chapter,
        section="§1",
        pdf_page=1,
        printed_page=1,
        statement="",
        source_chunks=source_chunks or [],
    )


def test_numbered_reference_produces_evidence_edge():
    target = node("b:定理1.2", "定理 1.2")
    source = node("b:定理1.1", "定理 1.1")
    index = NodeIndex([source, target])
    edges, issues = extract_numbered_edges(
        "p1", "由定理 1.1 可知结论成立。", "b:定理1.2", index, False
    )
    assert issues == []
    assert len(edges) == 1
    assert edges[0].from_id == "b:定理1.1"
    assert edges[0].to_id == "b:定理1.2"
    assert "定理 1.1" in edges[0].evidence.quote
    assert edges[0].evidence.quote in "由定理 1.1 可知结论成立。"


def test_numbered_ambiguous_reference_is_reported():
    target = node("b:定理1.3", "定理 1.3")
    source_a = node("b:定理1.1", "定理 1.1")
    source_b = node("b:定理1.1b", "定理 1.1")
    index = NodeIndex([source_a, source_b, target])
    edges, issues = extract_numbered_edges(
        "p1", "由定理 1.1 可知。", "b:定理1.3", index, False
    )
    assert edges == []
    assert issues[0]["type"] == "ambiguous_ref"


def test_named_alias_produces_edge_and_generic_alias_is_ignored():
    source = node("b:定理1.1", "定理 1.1", aliases=["定理 1.1", "Rolle 定理"])
    generic = node("b:定理1.2", "定理 1.2", aliases=["定理 1.2", "中值定理"])
    target = node("b:定理1.3", "定理 1.3")
    index = NodeIndex([source, generic, target])
    edges, _ = extract_named_edges(
        "p1", "由 Rolle 定理和 中值定理 可知。", "b:定理1.3", index, False
    )
    assert [e.from_id for e in edges] == ["b:定理1.1"]


def test_definition_alias_is_not_a_named_theorem_reference():
    definition = Node(
        id="b:定义1.1",
        kind="definition",
        subkind="definition",
        label="定义 1.1",
        title="数列极限",
        aliases=["定义 1.1", "数列极限"],
        book_id="b",
        chapter="第1章",
        section="§1",
        pdf_page=1,
        printed_page=1,
        statement="",
        source_chunks=[],
    )
    target = node("b:定理1.2", "定理 1.2")
    index = NodeIndex([definition, target])
    edges, _ = extract_named_edges(
        "p1", "由数列极限的定义可知。", "b:定理1.2", index, False
    )
    assert edges == []


def test_anaphora_resolves_to_preceding_tentative_edge():
    source = node("b:定理1.1", "定理 1.1", source_chunks=["c1"])
    target = node("b:定理1.2", "定理 1.2", source_chunks=["c2"])
    index = NodeIndex([source, target], chunk_order={"c1": 0, "c2": 1})
    edges, _ = extract_anaphora_edges(
        "p1", "由上述定理可知。", "b:定理1.2", index
    )
    assert len(edges) == 1
    assert edges[0].from_id == "b:定理1.1"
    assert edges[0].confidence == "tentative"
