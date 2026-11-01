from pathlib import Path

from proofmap.build import build_all
from proofmap.io import read_json

DEMO = Path(__file__).resolve().parents[1] / "examples" / "demo" / "chunks.jsonl"


def test_build_demo_produces_graph_and_audits(tmp_path: Path):
    summary = build_all(DEMO, tmp_path, books=["demo"])
    assert summary["nodes"] == 12
    assert summary["edges"] > 0
    assert summary["attachments"]["attached"] == 9
    for name in (
        "nodes.jsonl",
        "attachments.jsonl",
        "edges.jsonl",
        "graph.json",
        "attachment_audit.md",
        "edge_audit.md",
        "node_audit.md",
    ):
        assert (tmp_path / name).exists()
    graph = read_json(tmp_path / "graph.json")
    assert graph["metadata"]["book_titles"]["demo"] == "极小分析讲义"
    assert graph["metadata"]["counts"]["nodes"]["total"] == 12
    assert graph["metadata"]["counts"]["edges"]["total"] > 0


def test_build_is_deterministic(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    build_all(DEMO, first, books=["demo"])
    build_all(DEMO, second, books=["demo"])
    assert (first / "graph.json").read_bytes() == (second / "graph.json").read_bytes()


def test_book_filter_with_no_matches(tmp_path: Path):
    summary = build_all(DEMO, tmp_path, books=["missing"])
    assert summary["nodes"] == 0
    assert summary["edges"] == 0
    assert summary["attachments"] == {}
