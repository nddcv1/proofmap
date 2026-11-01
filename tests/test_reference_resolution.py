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


def test_dotted_label_resolves_book_wide():
    index = NodeIndex([node("b:定理1.2.3", "定理 1.2.3")])
    assert index.resolve_label("b", "第9章", "定理", "1.2.3") == ["b:定理1.2.3"]


def test_single_level_label_is_chapter_scoped():
    nodes = [
        node("b:定理1", "定理 1", "第1章"),
        node("b:定理1b", "定理 1", "第2章"),
    ]
    index = NodeIndex(nodes)
    assert index.resolve_label("b", "第1章", "定理", "1") == ["b:定理1"]


def test_alias_resolution_and_preceding():
    nodes = [
        node("b:定理1.1", "定理 1.1", aliases=["定理 1.1", "Rolle 定理"], source_chunks=["c1"]),
        node("b:定理1.2", "定理 1.2", source_chunks=["c2"]),
    ]
    index = NodeIndex(nodes, chunk_order={"c1": 0, "c2": 1})
    assert index.resolve_alias("b", "第1章", "Rolle 定理") == ["b:定理1.1"]
    assert index.preceding("b", "第1章", 1) == "b:定理1.1"
