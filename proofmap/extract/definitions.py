from __future__ import annotations

import re
from typing import Any

from proofmap.extract.evidence import make_evidence
from proofmap.model import Edge, Node
from proofmap.resolve import normalize

GENERIC_TERMS = {
    "函数",
    "集合",
    "连续",
    "极限",
    "导数",
    "积分",
    "数列",
    "映射",
    "区间",
    "定义",
}


def _eligible(term: str) -> bool:
    if term in GENERIC_TERMS:
        return False
    if re.search(r"[a-z]", term):
        return True
    return len(term) >= 3


def _terms(node: Node) -> list[str]:
    terms: set[str] = set()
    for alias in {node.title, node.label, *node.aliases}:
        key = normalize(alias)
        if key and _eligible(key):
            terms.add(key)
    return sorted(terms, key=len, reverse=True)


def _pattern(term: str) -> re.Pattern[str]:
    return re.compile(r"\s*".join(re.escape(char) for char in term), re.IGNORECASE)


def extract_definition_edges(
    nodes: list[Node],
    proof_contexts: dict[str, tuple[str, str]],
) -> tuple[list[Edge], list[dict[str, Any]]]:
    definitions = [node for node in nodes if node.kind == "definition"]
    theorems = [node for node in nodes if node.kind == "theorem"]
    edges: list[Edge] = []
    issues: list[dict[str, Any]] = []

    for theorem in theorems:
        proof_chunk, proof_text = proof_contexts.get(theorem.id, ("", ""))
        if proof_text:
            text = f"{theorem.statement}\n{proof_text}".strip()
            source_chunk = proof_chunk
        else:
            text = theorem.statement.strip()
            source_chunk = theorem.source_chunks[0] if theorem.source_chunks else ""
        if not text:
            continue

        seen: set[tuple[str, str]] = set()
        consumed: list[tuple[int, int]] = []
        for definition in definitions:
            if definition.book_id != theorem.book_id:
                continue
            for term in _terms(definition):
                if (definition.id, theorem.id) in seen:
                    break
                pattern = _pattern(term)
                for match in pattern.finditer(text):
                    start, end = match.start(), match.end()
                    if any(
                        not (end <= used_start or start >= used_end)
                        for used_start, used_end in consumed
                    ):
                        continue
                    consumed.append((start, end))
                    seen.add((definition.id, theorem.id))
                    edges.append(
                        Edge(
                            from_id=definition.id,
                            to_id=theorem.id,
                            type="definition_term",
                            confidence="inferred",
                            proof_chunk=source_chunk,
                            evidence=make_evidence(text, start, end),
                            source="rule",
                        )
                    )
                    break
                if (definition.id, theorem.id) in seen:
                    break

    return edges, issues
