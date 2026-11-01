from __future__ import annotations

import re
from typing import Any

from proofmap.extract.evidence import make_evidence
from proofmap.model import Edge
from proofmap.resolve import NodeIndex

_REF_RE = re.compile(
    r"(?P<kind>定理|引理|推论|命题|定义)\s*(?P<num>\d+(?:\.\d+)*[′'’*＊]*)"
)


def extract_numbered_edges(
    proof_chunk: str,
    proof_text: str,
    target_id: str,
    index: NodeIndex,
    include_ambiguous: bool = False,
) -> tuple[list[Edge], list[dict[str, Any]]]:
    target = index.by_id.get(target_id)
    if target is None:
        return [], [{"type": "missing_target", "proof_chunk": proof_chunk, "target": target_id}]

    edges: list[Edge] = []
    issues: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for match in _REF_RE.finditer(proof_text):
        kind = match.group("kind")
        number = match.group("num")
        ids = [
            node_id
            for node_id in index.resolve_label(
                target.book_id, target.chapter, kind, number
            )
            if node_id != target_id
        ]

        if not ids:
            issues.append(
                {
                    "type": "unresolved_ref",
                    "proof_chunk": proof_chunk,
                    "text": match.group(0),
                    "position": match.start(),
                }
            )
            continue

        if len(ids) > 1:
            issues.append(
                {
                    "type": "ambiguous_ref",
                    "proof_chunk": proof_chunk,
                    "text": match.group(0),
                    "candidates": ids,
                    "position": match.start(),
                }
            )
            if not include_ambiguous:
                continue
            chosen = ids[0]
            confidence = "tentative"
        else:
            chosen = ids[0]
            confidence = "explicit"

        key = (chosen, target_id)
        if key in seen:
            continue
        seen.add(key)
        edges.append(
            Edge(
                from_id=chosen,
                to_id=target_id,
                type="numbered_ref",
                confidence=confidence,
                proof_chunk=proof_chunk,
                evidence=make_evidence(proof_text, match.start(), match.end()),
                source="rule",
            )
        )

    return edges, issues
