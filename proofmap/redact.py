from __future__ import annotations

from typing import Any

NODE_TEXT_PLACEHOLDER = "公开结构版不包含教材原文。"
EDGE_TEXT_PLACEHOLDER = "公开结构版不包含原文证据。"
STRUCTURE_NOTICE = (
    "公开结构版：仅展示章节、编号、页码与依赖边；教材原文未上传。"
)


def public_label(node: dict[str, Any]) -> str:
    label = str(node.get("label", "")).strip()
    if any(character.isdigit() for character in label):
        return label
    suffix = str(node.get("id", "")).split(":")[-1]
    return f"{label} · {suffix}" if label else f"节点 · {suffix}"


def redact_graph(graph: dict[str, Any]) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    for node in graph.get("nodes", []):
        label = public_label(node)
        nodes.append(
            {
                "schema_version": node.get("schema_version", 1),
                "id": node.get("id", ""),
                "kind": node.get("kind", ""),
                "subkind": node.get("subkind", ""),
                "label": label,
                "title": label,
                "aliases": [label],
                "book_id": node.get("book_id", ""),
                "chapter": node.get("chapter", ""),
                "section": node.get("section", ""),
                "pdf_page": node.get("pdf_page", 0),
                "printed_page": node.get("printed_page", 0),
                "statement": NODE_TEXT_PLACEHOLDER,
                "proof": "",
                "source_chunks": [],
                "formula_review": False,
                "order": node.get("order", 0),
            }
        )

    edges: list[dict[str, Any]] = []
    for edge in graph.get("edges", []):
        edges.append(
            {
                "schema_version": edge.get("schema_version", 1),
                "from": edge.get("from", ""),
                "to": edge.get("to", ""),
                "type": edge.get("type", ""),
                "confidence": edge.get("confidence", ""),
                "proof_chunk": "",
                "evidence": {
                    "quote": EDGE_TEXT_PLACEHOLDER,
                    "char_start": 0,
                    "char_end": 0,
                },
                "source": edge.get("source", ""),
            }
        )

    metadata = graph.get("metadata", {})
    return {
        "schema_version": graph.get("schema_version", 1),
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "book_titles": dict(metadata.get("book_titles", {})),
            "books": list(metadata.get("books", [])),
            "default_book": metadata.get("default_book"),
            "counts": dict(metadata.get("counts", {})),
            "cycles": list(metadata.get("cycles", [])),
            "isolated_nodes": list(metadata.get("isolated_nodes", [])),
            "structure_only": True,
            "notice": STRUCTURE_NOTICE,
        },
    }
