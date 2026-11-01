from pathlib import Path

from proofmap.corrections import (
    apply_aliases,
    apply_attachment_corrections,
    apply_edge_corrections,
    load_corrections,
)
from proofmap.model import Edge, Evidence, Node, ProofAttachment


def node(id_, kind="theorem", label="定理 1.2"):
    return Node(
        id=id_,
        kind=kind,
        subkind=kind,
        label=label,
        title="",
        aliases=[label],
        book_id="b",
        chapter="第1章",
        section="§1",
        pdf_page=1,
        printed_page=1,
        statement="",
        source_chunks=[],
    )


def test_load_missing_returns_empty(tmp_path: Path):
    assert load_corrections(tmp_path / "missing.yaml") == {}


def test_corrections_apply_aliases_attachments_and_edges(tmp_path: Path):
    path = tmp_path / "corrections.yaml"
    path.write_text(
        """
proof_attachments:
  force:
    - proof_chunk: p1
      target: b:定理1.2
      reason: manual attach
  detach:
    - proof_chunk: p2
      reason: wrong target
aliases:
  b:定理1.2:
    - Rolle 定理
edges:
  add:
    - from: b:定义1.1
      to: b:定理1.2
      reason: manual edge
  remove:
    - from: b:定理9.9
      to: b:定理1.2
""",
        encoding="utf-8",
    )
    corrections = load_corrections(path)
    nodes = [
        node("b:定理1.2"),
        node("b:定义1.1", kind="definition", label="定义"),
    ]

    apply_aliases(nodes, corrections)
    assert "Rolle 定理" in nodes[0].aliases

    attachments = [
        ProofAttachment(
            proof_chunk="p1", target_id="", target_kind="", method="proximity",
            score=0.0, margin=0.0, status="unresolved", non_graph=False,
        ),
        ProofAttachment(
            proof_chunk="p2", target_id="b:定理1.2", target_kind="theorem",
            method="proximity", score=0.9, margin=0.3, status="attached",
            non_graph=False,
        ),
    ]
    attachments = apply_attachment_corrections(attachments, corrections, nodes)
    by_chunk = {a.proof_chunk: a for a in attachments}
    assert by_chunk["p1"].status == "attached"
    assert by_chunk["p1"].target_id == "b:定理1.2"
    assert by_chunk["p2"].status == "detached"

    edges = [
        Edge(from_id="b:定理9.9", to_id="b:定理1.2", type="numbered_ref",
             confidence="explicit", proof_chunk="p3",
             evidence=Evidence("", 0, 0), source="rule"),
    ]
    edges = apply_edge_corrections(edges, corrections)
    assert all(e.from_id != "b:定理9.9" for e in edges)
    assert any(e.source == "manual" and e.from_id == "b:定义1.1" for e in edges)
