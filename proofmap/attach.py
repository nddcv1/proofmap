from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from proofmap.model import Node, ProofAttachment

FAMILY_KINDS = {"theorem", "example", "exercise"}
DISTANCE_SCORES = {1: 0.40, 2: 0.30, 3: 0.22, 4: 0.15, 5: 0.10}
_CANDIDATE_LABEL_RE = re.compile(
    r"^\s*(定理|引理|推论|命题|例|例题|习题)\s*([0-9]+(?:\.[0-9]+)*[′'’*＊]*)?"
)
_INLINE_PROOF_RE = re.compile(r"(?:^|[\n。；;])\s*证明\s*[:：]?")
_WS_RE = re.compile(r"\s+")


@dataclass
class _Candidate:
    chunk: dict[str, Any]
    chunk_index: int
    distance: int
    score: float
    degraded: bool
    target_id: str
    target_kind: str


def _norm(text: str) -> str:
    return _WS_RE.sub("", text)


def _candidate_label(chunk: dict[str, Any], node: Node | None) -> str:
    if node is not None:
        return node.label
    match = _CANDIDATE_LABEL_RE.match(str(chunk.get("text", "")))
    if not match:
        return ""
    prefix, number = match.group(1), match.group(2) or ""
    return f"{prefix} {number}".strip()


def _target_id(
    chunk: dict[str, Any], node: Node | None, kind: str
) -> str:
    if node is not None:
        return node.id
    return f"{chunk.get('book_id', '')}:{kind}:{chunk.get('chunk_id', '')}"


def _score_candidate(
    proof: dict[str, Any],
    candidate: dict[str, Any],
    distance: int,
    node: Node | None,
) -> tuple[float, bool] | None:
    proof_section = str(proof.get("section") or "")
    candidate_section = str(candidate.get("section") or "")
    proof_chapter = str(proof.get("chapter") or "")
    candidate_chapter = str(candidate.get("chapter") or "")

    if proof_chapter and candidate_chapter and proof_chapter != candidate_chapter:
        return None

    degraded = False
    if proof_section and candidate_section:
        if proof_section != candidate_section:
            return None
        score = 0.45
    else:
        score = 0.25
        degraded = True

    score += DISTANCE_SCORES[distance]

    label = _candidate_label(candidate, node)
    if label and _norm(label) in _norm(str(proof.get("text", ""))):
        score += 0.30

    if _INLINE_PROOF_RE.search(str(candidate.get("text", ""))):
        score -= 0.50

    return max(0.0, min(1.0, score)), degraded


def attach_proofs(
    chunks: list[dict[str, Any]], nodes: list[Node]
) -> list[ProofAttachment]:
    node_by_chunk: dict[str, Node] = {}
    for node in nodes:
        for chunk_id in node.source_chunks:
            node_by_chunk[chunk_id] = node

    attachments: list[ProofAttachment] = []
    for index, proof in enumerate(chunks):
        if proof.get("kind") != "proof":
            continue

        candidates: list[_Candidate] = []
        for distance in range(1, 6):
            if index - distance < 0:
                break
            candidate = chunks[index - distance]
            if candidate.get("book_id") != proof.get("book_id"):
                break

            # Do not cross a real section boundary while walking backwards.
            proof_section = str(proof.get("section") or "")
            candidate_section = str(candidate.get("section") or "")
            if proof_section and candidate_section and proof_section != candidate_section:
                break
            if candidate.get("kind") not in FAMILY_KINDS:
                continue

            node = node_by_chunk.get(str(candidate.get("chunk_id", "")))
            scored = _score_candidate(proof, candidate, distance, node)
            if scored is None:
                break
            score, degraded = scored
            candidate_kind = str(candidate.get("kind"))
            candidates.append(
                _Candidate(
                    chunk=candidate,
                    chunk_index=index - distance,
                    distance=distance,
                    score=score,
                    degraded=degraded,
                    target_id=_target_id(candidate, node, candidate_kind),
                    target_kind=candidate_kind,
                )
            )

        if not candidates:
            attachments.append(
                ProofAttachment(
                    proof_chunk=str(proof.get("chunk_id", "")),
                    target_id="",
                    target_kind="",
                    method="proximity",
                    score=0.0,
                    margin=0.0,
                    status="unresolved",
                    non_graph=False,
                    evidence="no theorem/example/exercise within 5 chunks",
                )
            )
            continue

        candidates.sort(key=lambda c: (-c.score, c.distance, c.chunk_index))
        top = candidates[0]
        second = candidates[1] if len(candidates) > 1 else None
        margin = top.score - second.score if second else top.score

        nearest_exception = top.distance == 1 and top.score >= 0.55
        if (
            top.score >= 0.55
            and (margin >= 0.15 or nearest_exception)
            and not top.degraded
        ):
            status = "attached"
        else:
            status = "ambiguous"

        attachments.append(
            ProofAttachment(
                proof_chunk=str(proof.get("chunk_id", "")),
                target_id=top.target_id,
                target_kind=top.target_kind,
                method="proximity",
                score=round(top.score, 4),
                margin=round(margin, 4),
                status=status,
                non_graph=top.target_kind in {"example", "exercise"},
                evidence=(
                    f"distance={top.distance}; score={top.score:.2f}; "
                    f"margin={margin:.2f}; degraded={top.degraded}"
                ),
            )
        )

    return attachments


def apply_attachments(
    nodes: list[Node],
    attachments: list[ProofAttachment],
    chunks: list[dict[str, Any]],
) -> None:
    chunk_by_id = {str(c.get("chunk_id", "")): c for c in chunks}
    proofs_by_target: dict[str, list[str]] = {}
    for attachment in attachments:
        if attachment.status != "attached" or attachment.non_graph:
            continue
        if not attachment.target_id:
            continue
        chunk = chunk_by_id.get(attachment.proof_chunk)
        if chunk is None:
            continue
        proofs_by_target.setdefault(attachment.target_id, []).append(
            str(chunk.get("text", "")).strip()
        )

    for node in nodes:
        texts = proofs_by_target.get(node.id, [])
        node.proof = "\n\n".join(text for text in texts if text)
