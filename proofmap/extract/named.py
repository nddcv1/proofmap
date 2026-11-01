from __future__ import annotations

import re
from typing import Any

from proofmap.extract.evidence import make_evidence
from proofmap.model import Edge
from proofmap.resolve import NodeIndex, normalize

GENERIC_ALIASES = {
    "中值定理",
    "微分中值定理",
    "基本定理",
    "定理",
    "引理",
    "推论",
    "命题",
    "定义",
    "公式",
    "不等式",
}
_NUMERIC_LABEL_RE = re.compile(r"(定理|引理|推论|命题|定义)\d+(?:\.\d+)*[′'’*＊]*")


def _eligible(alias: str) -> bool:
    if alias in GENERIC_ALIASES:
        return False
    if _NUMERIC_LABEL_RE.fullmatch(alias):
        return False
    if re.search(r"[a-z]", alias):
        return len(alias) >= 3
    return len(alias) >= 4


def _pattern(alias: str) -> re.Pattern[str]:
    return re.compile(r"\s*".join(re.escape(char) for char in alias), re.IGNORECASE)


def extract_named_edges(
    proof_chunk: str,
    proof_text: str,
    target_id: str,
    index: NodeIndex,
    include_ambiguous: bool = False,
) -> tuple[list[Edge], list[dict[str, Any]]]:
    target = index.by_id.get(target_id)
    if target is None:
        return [], [{"type": "missing_target", "proof_chunk": proof_chunk, "target": target_id}]

    aliases = index.aliases_for_book(target.book_id)
    candidates = sorted(
        (alias for alias in aliases if _eligible(alias)),
        key=len,
        reverse=True,
    )

    edges: list[Edge] = []
    issues: list[dict[str, Any]] = []
    consumed: list[tuple[int, int]] = []
    seen: set[tuple[str, str]] = set()

    for alias in candidates:
        pattern = _pattern(alias)
        for match in pattern.finditer(proof_text):
            start, end = match.start(), match.end()
            if any(not (end <= used_start or start >= used_end) for used_start, used_end in consumed):
                continue
            consumed.append((start, end))

            ids = [
                node_id
                for node_id in index.resolve_alias(target.book_id, target.chapter, alias)
                if node_id != target_id
                and index.by_id.get(node_id) is not None
                and index.by_id[node_id].kind == "theorem"
            ]
            if not ids:
                continue
            if len(ids) > 1:
                issues.append(
                    {
                        "type": "ambiguous_alias",
                        "proof_chunk": proof_chunk,
                        "text": match.group(0),
                        "candidates": ids,
                        "position": start,
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
                    type="named_ref",
                    confidence=confidence,
                    proof_chunk=proof_chunk,
                    evidence=make_evidence(proof_text, start, end),
                    source="rule",
                )
            )

    return edges, issues
