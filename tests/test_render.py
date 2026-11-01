from pathlib import Path

from proofmap.render import render_html


def graph():
    return {
        "schema_version": 1,
        "nodes": [
            {
                "id": "b:定理1.1",
                "kind": "theorem",
                "subkind": "theorem",
                "label": "定理 1.1",
                "title": "示例",
                "aliases": ["定理 1.1"],
                "book_id": "b",
                "chapter": "第1章",
                "section": "§1",
                "pdf_page": 1,
                "printed_page": 1,
                "statement": "设 $x>0$。",
                "proof": "",
                "source_chunks": ["c1"],
                "formula_review": False,
                "order": 0,
            }
        ],
        "edges": [],
        "metadata": {"book_titles": {"b": "Demo"}},
    }


def test_render_embeds_data_and_vendor(tmp_path: Path):
    out = tmp_path / "g.html"
    render_html(graph(), out)
    html = out.read_text(encoding="utf-8")
    assert "__GRAPH_JSON__" not in html
    assert "定理 1.1" in html
    assert "cytoscape" in html.lower()
    assert "<script src=" not in html
    assert 'src="http' not in html
    assert out.stat().st_size > 100_000


def test_render_escapes_script_closer(tmp_path: Path):
    data = graph()
    data["nodes"][0]["statement"] = "危险 </script><script>alert(1)</script>"
    out = tmp_path / "g.html"
    render_html(data, out)
    html = out.read_text(encoding="utf-8")
    assert "</script><script>alert(1)" not in html
