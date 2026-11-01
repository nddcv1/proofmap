from proofmap.model import Edge, Evidence, Node


def test_edge_serializes_from_to_and_roundtrips():
    edge = Edge(
        from_id="a",
        to_id="b",
        type="numbered_ref",
        confidence="explicit",
        proof_chunk="p1",
        evidence=Evidence("由定理 a 可知", 0, 7),
        source="rule",
    )
    data = edge.to_dict()
    assert data["from"] == "a"
    assert data["to"] == "b"
    assert Edge.from_dict(data) == edge


def test_node_defaults_and_roundtrip():
    node = Node(
        id="book:定理1.1",
        kind="theorem",
        subkind="theorem",
        label="定理 1.1",
        title="示例",
        aliases=["定理 1.1"],
        book_id="book",
        chapter="第1章",
        section="1.1",
        pdf_page=1,
        printed_page=1,
        statement="设 x>0。",
        source_chunks=["c1"],
    )
    assert node.proof == ""
    assert Node.from_dict(node.to_dict()) == node
