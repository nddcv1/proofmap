from pathlib import Path

from proofmap.cli import main

DEMO = Path(__file__).resolve().parents[1] / "examples" / "demo" / "chunks.jsonl"
GOLD = Path(__file__).resolve().parents[1] / "gold" / "demo_gold.yaml"


def test_build_render_query_eval(tmp_path: Path, capsys):
    build_dir = tmp_path / "build"
    assert main(["build", "--chunks", str(DEMO), "--out", str(build_dir), "--book", "demo"]) == 0
    assert (build_dir / "graph.json").exists()

    html = tmp_path / "demo.html"
    assert main(["render", "--build", str(build_dir), "--out", str(html)]) == 0
    assert html.exists()

    assert main([
        "query", "prereq", "demo:定理1.4",
        "--build", str(build_dir),
    ]) == 0
    output = capsys.readouterr().out
    assert "定义 1.1" in output

    assert main([
        "eval", "--build", str(build_dir), "--gold", str(GOLD),
    ]) == 0
    output = capsys.readouterr().out
    assert "precision" in output
    assert "1.000" in output


def test_render_structure_only_redacts_text(tmp_path: Path):
    build_dir = tmp_path / "build"
    assert main(["build", "--chunks", str(DEMO), "--out", str(build_dir), "--book", "demo"]) == 0
    html = tmp_path / "structure.html"
    assert main([
        "render", "--build", str(build_dir), "--out", str(html), "--structure-only",
    ]) == 0
    text = html.read_text(encoding="utf-8")
    assert "公开结构版" in text
    assert "由定义 1.1" not in text
    assert "定理 1.1" in text


def test_build_missing_chunks_returns_1(tmp_path: Path, capsys):
    assert main([
        "build", "--chunks", str(tmp_path / "missing.jsonl"), "--out", str(tmp_path / "out"),
    ]) == 1
    assert "error" in capsys.readouterr().err.lower()


def test_query_unknown_node_returns_1(tmp_path: Path, capsys):
    build_dir = tmp_path / "build"
    assert main(["build", "--chunks", str(DEMO), "--out", str(build_dir), "--book", "demo"]) == 0
    assert main([
        "query", "prereq", "demo:不存在", "--build", str(build_dir),
    ]) == 1
    assert "not found" in capsys.readouterr().err.lower()
