import json
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
    assert graph["metadata"]["default_book"] == "demo"
    assert graph["metadata"]["counts"]["nodes"]["total"] == 12
    assert graph["metadata"]["counts"]["edges"]["total"] > 0


def test_build_is_deterministic(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    build_all(DEMO, first, books=["demo"])
    build_all(DEMO, second, books=["demo"])
    assert (first / "graph.json").read_bytes() == (second / "graph.json").read_bytes()


def test_default_book_is_the_largest(tmp_path: Path):
    chunks = tmp_path / "chunks.jsonl"
    rows = [
        {
            "chunk_id": "a1", "book_id": "a", "book_title": "A", "short": "A",
            "subject": "数学分析", "pdf_page": 1, "printed_page": 1,
            "chapter": "第1章", "section": "§1", "subsection": "",
            "kind": "theorem", "text": "定理 1.1 甲。", "plain_text": "",
            "source_image": "", "formula_review": False,
        },
        {
            "chunk_id": "b1", "book_id": "b", "book_title": "B", "short": "B",
            "subject": "数学分析", "pdf_page": 1, "printed_page": 1,
            "chapter": "第1章", "section": "§1", "subsection": "",
            "kind": "theorem", "text": "定理 1.1 乙。", "plain_text": "",
            "source_image": "", "formula_review": False,
        },
        {
            "chunk_id": "b2", "book_id": "b", "book_title": "B", "short": "B",
            "subject": "数学分析", "pdf_page": 1, "printed_page": 1,
            "chapter": "第1章", "section": "§1", "subsection": "",
            "kind": "definition", "text": "定义 1.2 丙。", "plain_text": "",
            "source_image": "", "formula_review": False,
        },
    ]
    chunks.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )
    build_all(chunks, tmp_path / "out")
    graph = read_json(tmp_path / "out" / "graph.json")
    assert graph["metadata"]["default_book"] == "b"


def test_book_filter_with_no_matches(tmp_path: Path):
    summary = build_all(DEMO, tmp_path, books=["missing"])
    assert summary["nodes"] == 0
    assert summary["edges"] == 0
    assert summary["attachments"] == {}
