from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from proofmap.model import Edge, Node

STRICT_EDGE_TYPES = {"numbered_ref", "named_ref", "anaphora_ref", "llm", "manual"}
_TYPE_PRIORITY = {
    "manual": 60,
    "numbered_ref": 50,
    "named_ref": 40,
    "llm": 30,
    "anaphora_ref": 20,
    "definition_term": 10,
}
_CONFIDENCE_PRIORITY = {
    "confirmed": 4,
    "explicit": 3,
    "inferred": 2,
    "tentative": 1,
}


def dedupe_edges(edges: list[Edge]) -> list[Edge]:
    best: dict[tuple[str, str], tuple[tuple[int, int], Edge]] = {}
    for edge in edges:
        key = (edge.from_id, edge.to_id)
        rank = (
            _TYPE_PRIORITY.get(edge.type, 0),
            _CONFIDENCE_PRIORITY.get(edge.confidence, 0),
        )
        if key not in best or rank > best[key][0]:
            best[key] = (rank, edge)
    return [
        edge
        for _, edge in sorted(
            best.values(), key=lambda item: (item[1].to_id, item[1].from_id, item[1].type)
        )
    ]


def _edge_parts(edge: Edge | dict[str, Any]) -> tuple[str, str, str, str]:
    if isinstance(edge, Edge):
        return edge.from_id, edge.to_id, edge.type, edge.confidence
    return (
        str(edge.get("from", edge.get("from_id", ""))),
        str(edge.get("to", edge.get("to_id", ""))),
        str(edge.get("type", "")),
        str(edge.get("confidence", "")),
    )


def _node_id(node: Node | str) -> str:
    return node.id if isinstance(node, Node) else str(node)


def find_cycles(
    nodes: list[Node | str], edges: list[Edge | dict[str, Any]]
) -> list[list[str]]:
    node_ids = {_node_id(node) for node in nodes}
    adjacency: dict[str, set[str]] = defaultdict(set)

    for edge in edges:
        source, target, edge_type, confidence = _edge_parts(edge)
        if edge_type not in STRICT_EDGE_TYPES or confidence == "tentative":
            continue
        if not source or not target:
            continue
        node_ids.add(source)
        node_ids.add(target)
        adjacency[source].add(target)

    color: dict[str, int] = {}
    path: list[str] = []
    cycles: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()

    def canonical(cycle: list[str]) -> tuple[str, ...]:
        if not cycle:
            return ()
        start = min(range(len(cycle)), key=lambda index: cycle[index])
        return tuple(cycle[start:] + cycle[:start])

    def visit(node: str) -> None:
        color[node] = 1
        path.append(node)
        for target in sorted(adjacency.get(node, ())):
            state = color.get(target, 0)
            if state == 0:
                visit(target)
            elif state == 1:
                index = path.index(target)
                cycle = path[index:]
                key = canonical(cycle)
                if key not in seen:
                    seen.add(key)
                    cycles.append(list(cycle))
        path.pop()
        color[node] = 2

    for node_id in sorted(node_ids):
        if color.get(node_id, 0) == 0:
            visit(node_id)

    return cycles


def isolated_nodes(
    nodes: list[Node | str], edges: list[Edge | dict[str, Any]]
) -> list[str]:
    incident: set[str] = set()
    for edge in edges:
        source, target, _, _ = _edge_parts(edge)
        if source:
            incident.add(source)
        if target:
            incident.add(target)
    return sorted(
        node_id for node_id in (_node_id(node) for node in nodes) if node_id not in incident
    )


def build_graph(
    nodes: list[Node],
    attachments: list[Any],
    edges: list[Edge],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = dict(metadata or {})
    chunk_order: dict[str, int] = metadata.pop("chunk_order", {})

    def order_of(node: Node) -> int:
        if node.source_chunks:
            return chunk_order.get(node.source_chunks[0], 10**9)
        return 10**9

    sorted_nodes = sorted(
        nodes, key=lambda node: (node.book_id, order_of(node), node.id)
    )
    node_dicts: list[dict[str, Any]] = []
    for node in sorted_nodes:
        payload = node.to_dict()
        payload["order"] = order_of(node)
        node_dicts.append(payload)

    sorted_edges = sorted(
        edges,
        key=lambda edge: (edge.to_id, edge.from_id, edge.type, edge.confidence),
    )
    edge_dicts = [edge.to_dict() for edge in sorted_edges]

    status_counts = dict(Counter(attachment.status for attachment in attachments))
    counts = {
        "nodes": {
            "total": len(nodes),
            "by_kind": dict(Counter(node.kind for node in nodes)),
        },
        "edges": {
            "total": len(edges),
            "by_type": dict(Counter(edge.type for edge in edges)),
            "by_confidence": dict(Counter(edge.confidence for edge in edges)),
        },
        "attachments": {
            "total": len(attachments),
            "by_status": status_counts,
            **status_counts,
            "non_graph": sum(1 for attachment in attachments if attachment.non_graph),
        },
    }

    cycles = find_cycles(nodes, edges)
    metadata.update(
        {
            "counts": counts,
            "cycles": cycles,
            "isolated_nodes": isolated_nodes(nodes, edges),
        }
    )

    return {
        "schema_version": 1,
        "nodes": node_dicts,
        "edges": edge_dicts,
        "metadata": metadata,
    }
