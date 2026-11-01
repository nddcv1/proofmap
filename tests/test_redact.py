import json

from proofmap.redact import redact_graph


def sample_graph():
    return {
        "schema_version": 1,
        "nodes": [
            {
                "schema_version": 1,
                "id": "b:定理1.1",
                "kind": "theorem",
                "subkind": "theorem",
                "label": "定理 1.1",
                "title": "秘密定理标题",
                "aliases": ["定理 1.1", "秘密别名"],
                "book_id": "b",
                "chapter": "第1章",
                "section": "§1",
                "pdf_page": 1,
                "printed_page": 1,
                "statement": "秘密陈述内容",
                "proof": "秘密证明内容",
                "source_chunks": ["c1"],
                "formula_review": True,
                "order": 0,
            },
            {
                "schema_version": 1,
                "id": "b:第1章:002",
                "kind": "definition",
                "subkind": "definition",
                "label": "定义",
                "title": "秘密定义标题",
                "aliases": ["秘密定义别名"],
                "book_id": "b",
                "chapter": "第1章",
                "section": "§1",
                "pdf_page": 2,
                "printed_page": 2,
                "statement": "秘密定义内容",
                "proof": "",
                "source_chunks": ["c2"],
                "formula_review": False,
                "order": 1,
            },
        ],
        "edges": [
            {
                "schema_version": 1,
                "from": "b:第1章:002",
                "to": "b:定理1.1",
                "type": "numbered_ref",
                "confidence": "explicit",
                "proof_chunk": "c3",
                "evidence": {
                    "quote": "秘密证据",
                    "char_start": 0,
                    "char_end": 4,
                },
                "source": "rule",
            }
        ],
        "metadata": {
            "book_titles": {"b": "示例教材"},
            "books": ["b"],
            "default_book": "b",
            "counts": {"nodes": {"total": 2}},
            "cycles": [],
            "isolated_nodes": [],
            "source_chunks": 99,
        },
    }


def test_redact_removes_all_text_fields():
    redacted = redact_graph(sample_graph())
    blob = json.dumps(redacted, ensure_ascii=False)
    for secret in (
        "秘密陈述内容",
        "秘密证明内容",
        "秘密别名",
        "秘密定理标题",
        "秘密证据",
        "秘密定义内容",
        "秘密定义别名",
    ):
        assert secret not in blob
    assert redacted["nodes"][0]["statement"] != "秘密陈述内容"
    assert redacted["nodes"][0]["proof"] == ""
    assert redacted["nodes"][0]["source_chunks"] == []
    assert redacted["nodes"][0]["aliases"] == ["定理 1.1"]
    assert redacted["edges"][0]["proof_chunk"] == ""
    assert redacted["edges"][0]["evidence"]["quote"] != "秘密证据"
    assert redacted["metadata"]["structure_only"] is True
    assert "source_chunks" not in redacted["metadata"]


def test_generic_labels_get_unique_id_suffix():
    redacted = redact_graph(sample_graph())
    labels = [node["label"] for node in redacted["nodes"]]
    assert labels == ["定理 1.1", "定义 · 002"]
    assert len(set(labels)) == len(labels)


def test_public_label_prefers_short_display_name():
    graph = sample_graph()
    graph["nodes"][0]["display_name"] = "极限唯一性"
    redacted = redact_graph(graph)
    assert redacted["nodes"][0]["label"] == "极限唯一性"
    assert redacted["nodes"][0]["display_name"] == "极限唯一性"
