from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from proofmap.model import Edge, Evidence, Node, ProofAttachment


def load_corrections(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    source = Path(path)
    if not source.exists():
        return {}
    data = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def apply_aliases(nodes: list[Node], corrections: dict[str, Any]) -> None:
    mapping = corrections.get("aliases") or {}
    node_by_id = {node.id: node for node in nodes}
    for node_id, aliases in mapping.items():
        node = node_by_id.get(str(node_id))
        if node is None or not isinstance(aliases, list):
            continue
        current = list(node.aliases)
        for alias in aliases:
            if isinstance(alias, str) and alias and alias not in current:
                current.append(alias)
        node.aliases = current


def apply_attachment_corrections(
    attachments: list[ProofAttachment],
    corrections: dict[str, Any],
    nodes: list[Node],
) -> list[ProofAttachment]:
    section = corrections.get("proof_attachments") or {}
    node_by_id = {node.id: node for node in nodes}
    result = {attachment.proof_chunk: attachment for attachment in attachments}

    for entry in section.get("force") or []:
        proof_chunk = str(entry.get("proof_chunk", ""))
        target = str(entry.get("target", ""))
        node = node_by_id.get(target)
        if not proof_chunk or node is None:
            continue
        result[proof_chunk] = ProofAttachment(
            proof_chunk=proof_chunk,
            target_id=target,
            target_kind=node.kind,
            method="manual",
            score=1.0,
            margin=1.0,
            status="attached",
            non_graph=False,
            evidence=str(entry.get("reason", "")),
        )

    for entry in section.get("detach") or []:
        proof_chunk = str(entry.get("proof_chunk", ""))
        if not proof_chunk:
            continue
        result[proof_chunk] = ProofAttachment(
            proof_chunk=proof_chunk,
            target_id="",
            target_kind="",
            method="manual",
            score=0.0,
            margin=0.0,
            status="detached",
            non_graph=False,
            evidence=str(entry.get("reason", "")),
        )

    return sorted(result.values(), key=lambda attachment: attachment.proof_chunk)


def apply_edge_corrections(
    edges: list[Edge], corrections: dict[str, Any]
) -> list[Edge]:
    section = corrections.get("edges") or {}
    result = list(edges)

    for entry in section.get("remove") or []:
        source = str(entry.get("from", ""))
        target = str(entry.get("to", ""))
        edge_type = entry.get("type")
        result = [
            edge
            for edge in result
            if not (
                edge.from_id == source
                and edge.to_id == target
                and (edge_type is None or edge.type == edge_type)
            )
        ]

    for entry in section.get("add") or []:
        source = str(entry.get("from", ""))
        target = str(entry.get("to", ""))
        if not source or not target:
            continue
        edge_type = str(entry.get("type", "manual"))
        duplicate = any(
            edge.from_id == source
            and edge.to_id == target
            and edge.type == edge_type
            and edge.source == "manual"
            for edge in result
        )
        if duplicate:
            continue
        result.append(
            Edge(
                from_id=source,
                to_id=target,
                type=edge_type,
                confidence="confirmed",
                proof_chunk="",
                evidence=Evidence("", 0, 0),
                source="manual",
            )
        )

    return result
