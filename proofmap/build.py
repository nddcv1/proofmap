from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from proofmap.adapters.mathkb import extract_nodes, load_chunks
from proofmap.attach import apply_attachments, attach_proofs
from proofmap.audit import write_audits
from proofmap.corrections import (
    apply_aliases,
    apply_attachment_corrections,
    apply_edge_corrections,
    load_corrections,
)
from proofmap.extract.anaphora import extract_anaphora_edges
from proofmap.extract.definitions import extract_definition_edges
from proofmap.extract.named import extract_named_edges
from proofmap.extract.numbered import extract_numbered_edges
from proofmap.graph import build_graph, dedupe_edges
from proofmap.io import write_json, write_jsonl
from proofmap.model import Edge
from proofmap.names import apply_display_names
from proofmap.resolve import NodeIndex


def build_all(
    chunks_path: str | Path,
    out_dir: str | Path,
    books: list[str] | None = None,
    include_ambiguous: bool = False,
    corrections_path: str | Path | None = None,
    names_path: str | Path | None = None,
) -> dict[str, Any]:
    chunks = load_chunks(chunks_path)
    if books:
        selected = set(books)
        chunks = [chunk for chunk in chunks if chunk.get("book_id") in selected]

    nodes, node_issues = extract_nodes(chunks)
    corrections = load_corrections(corrections_path)
    apply_aliases(nodes, corrections)
    file_names = load_corrections(names_path).get("names") or {}
    name_overrides = {**file_names, **(corrections.get("names") or {})}
    apply_display_names(nodes, name_overrides)

    attachments = attach_proofs(chunks, nodes)
    attachments = apply_attachment_corrections(attachments, corrections, nodes)
    apply_attachments(nodes, attachments, chunks)

    chunk_order = {
        str(chunk.get("chunk_id", "")): index for index, chunk in enumerate(chunks)
    }
    chunk_by_id = {str(chunk.get("chunk_id", "")): chunk for chunk in chunks}
    index = NodeIndex(nodes, chunk_order)

    edges: list[Edge] = []
    edge_issues: list[dict[str, Any]] = []
    proof_contexts: dict[str, tuple[str, str]] = {}

    for attachment in attachments:
        if attachment.status != "attached" or attachment.non_graph:
            continue
        chunk = chunk_by_id.get(attachment.proof_chunk)
        if chunk is None:
            continue
        text = str(chunk.get("text", ""))
        if attachment.target_id not in proof_contexts:
            proof_contexts[attachment.target_id] = (attachment.proof_chunk, text)

        found, issues = extract_numbered_edges(
            attachment.proof_chunk,
            text,
            attachment.target_id,
            index,
            include_ambiguous,
        )
        edges.extend(found)
        edge_issues.extend(issues)

        found, issues = extract_named_edges(
            attachment.proof_chunk,
            text,
            attachment.target_id,
            index,
            include_ambiguous,
        )
        edges.extend(found)
        edge_issues.extend(issues)

        found, issues = extract_anaphora_edges(
            attachment.proof_chunk,
            text,
            attachment.target_id,
            index,
        )
        edges.extend(found)
        edge_issues.extend(issues)

    definition_edges, definition_issues = extract_definition_edges(
        nodes, proof_contexts
    )
    edges.extend(definition_edges)
    edge_issues.extend(definition_issues)

    edges = apply_edge_corrections(edges, corrections)
    edges = dedupe_edges(edges)

    book_titles: dict[str, str] = {}
    for chunk in chunks:
        book_id = str(chunk.get("book_id", ""))
        book_titles.setdefault(book_id, str(chunk.get("book_title", book_id)))

    book_counts = Counter(node.book_id for node in nodes)
    default_book = (
        sorted(book_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
        if book_counts
        else None
    )

    metadata = {
        "book_titles": book_titles,
        "books": sorted(book_titles),
        "default_book": default_book,
        "source_chunks": len(chunks),
        "chunk_order": chunk_order,
    }
    graph = build_graph(nodes, attachments, edges, metadata)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "nodes.jsonl", nodes)
    write_jsonl(out / "attachments.jsonl", attachments)
    write_jsonl(out / "edges.jsonl", edges)
    write_json(out / "graph.json", graph)
    write_audits(
        out,
        nodes,
        attachments,
        edges,
        graph["metadata"]["cycles"],
        edge_issues=edge_issues,
        node_issues=node_issues,
    )

    return {
        "build_dir": str(out),
        "nodes": len(nodes),
        "edges": len(edges),
        "attachments": dict(Counter(attachment.status for attachment in attachments)),
        "cycles": len(graph["metadata"]["cycles"]),
        "edge_issues": len(edge_issues),
    }
