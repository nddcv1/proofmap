from __future__ import annotations

import re
from typing import Any

from proofmap.extract.evidence import make_evidence
from proofmap.model import Edge
from proofmap.resolve import NodeIndex

_PATTERNS = [
    re.compile(pattern)
    for pattern in ("上述定理", "前一定理", "上节定理", "由上述", "上述结论")
]


def extract_anaphora_edges(
    proof_chunk: str,
    proof_text: str,
    target_id: str,
    index: NodeIndex,
) -> tuple[list[Edge], list[dict[str, Any]]]:
    target = index.by_id.get(target_id)
    if target is None:
        return [], [{"type": "missing_target", "proof_chunk": proof_chunk, "target": target_id}]

    order = index.order.get(target_id, 10**9)
    preceding = index.preceding(target.book_id, target.chapter, order)

    edges: list[Edge] = []
    issues: list[dict[str, Any]] = []
    evidence = None
    for pattern in _PATTERNS:
        match = pattern.search(proof_text)
        if match:
            evidence = make_evidence(proof_text, match.start(), match.end())
            break

    if evidence is None:
        return edges, issues

    if preceding is None:
        issues.append(
            {
                "type": "unresolved_anaphora",
                "proof_chunk": proof_chunk,
                "text": evidence.quote,
            }
        )
        return edges, issues

    edges.append(
        Edge(
            from_id=preceding,
            to_id=target_id,
            type="anaphora_ref",
            confidence="tentative",
            proof_chunk=proof_chunk,
            evidence=evidence,
            source="rule",
        )
    )
    return edges, issues
