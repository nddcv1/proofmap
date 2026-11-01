from pathlib import Path

from proofmap.audit import write_audits
from proofmap.graph import build_graph, dedupe_edges, find_cycles, isolated_nodes
from proofmap.model import Edge, Evidence, Node, ProofAttachment


def edge(a, b, type_="numbered_ref", confidence="explicit"):
    return Edge(
        from_id=a,
        to_id=b,
        type=type_,
        confidence=confidence,
        proof_chunk="p",
        evidence=Evidence("", 0, 0),
        source="rule",
    )


def node(id_, source_chunk="c1"):
    return Node(
        id=id_,
        kind="theorem",
        subkind="theorem",
        label=id_,
        title="",
        aliases=[id_],
        book_id="b",
        chapter="第1章",
        section="§1",
        pdf_page=1,
        printed_page=1,
        statement="",
        source_chunks=[source_chunk],
    )


def test_detects_cycle():
    assert find_cycles(["a", "b"], [edge("a", "b"), edge("b", "a")])


def test_definition_edges_do_not_form_strict_cycles():
    edges = [
        edge("a", "b"),
        edge("b", "a", type_="definition_term", confidence="inferred"),
    ]
    assert find_cycles(["a", "b"], edges) == []


def test_isolated_nodes():
    nodes = [node("a", "c1"), node("b", "c2"), node("c", "c3")]
    assert isolated_nodes(nodes, [edge("a", "b")]) == ["c"]


def test_dedupe_prefers_stronger_evidence():
    edges = [edge("a", "b", "named_ref"), edge("a", "b", "numbered_ref")]
    result = dedupe_edges(edges)
    assert len(result) == 1
    assert result[0].type == "numbered_ref"


def test_build_graph_sorts_and_counts():
    nodes = [node("b", "c2"), node("a", "c1")]
    attachments = [
        ProofAttachment(
            proof_chunk="p", target_id="a", target_kind="theorem",
            method="proximity", score=0.9, margin=0.3, status="attached",
            non_graph=False,
        )
    ]
    graph = build_graph(
        nodes, attachments, [edge("a", "b")], {"chunk_order": {"c1": 0, "c2": 1}}
    )
    assert [item["id"] for item in graph["nodes"]] == ["a", "b"]
    assert graph["edges"][0]["from"] == "a"
    assert graph["metadata"]["counts"]["attachments"]["attached"] == 1


def test_write_audits(tmp_path: Path):
    write_audits(
        tmp_path,
        [node("a"), node("b", "c2")],
        [],
        [edge("a", "b")],
        [["a", "b"]],
        edge_issues=[{"type": "unresolved_ref", "proof_chunk": "p", "text": "定理 9.9"}],
        node_issues=["duplicate numeric label 定理 1.1 in b"],
    )
    for name in ("attachment_audit.md", "edge_audit.md", "node_audit.md"):
        assert (tmp_path / name).exists()
    assert "a" in (tmp_path / "edge_audit.md").read_text(encoding="utf-8")
