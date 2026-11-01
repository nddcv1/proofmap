from __future__ import annotations

from collections import defaultdict
from typing import Any

from proofmap.model import Edge, ProofAttachment


def evaluate(
    attachments: list[ProofAttachment],
    edges: list[Edge],
    gold: dict[str, Any],
) -> dict[str, Any]:
    proofs = list(gold.get("proofs") or [])
    if not proofs:
        return {
            "n_gold": 0,
            "attachment_accuracy": None,
            "edge_precision": None,
            "edge_recall": None,
            "tp": 0,
            "fp": 0,
            "fn": 0,
        }

    attachment_by_chunk = {attachment.proof_chunk: attachment for attachment in attachments}
    correct_attachments = 0
    for item in proofs:
        attachment = attachment_by_chunk.get(str(item.get("proof_chunk", "")))
        if (
            attachment is not None
            and attachment.status == "attached"
            and attachment.target_id == item.get("target_id")
        ):
            correct_attachments += 1

    predicted_by_proof: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        if edge.proof_chunk:
            predicted_by_proof[edge.proof_chunk].add(edge.from_id)

    true_positive = 0
    false_positive = 0
    false_negative = 0
    for item in proofs:
        proof_chunk = str(item.get("proof_chunk", ""))
        expected = set(item.get("used") or [])
        predicted = predicted_by_proof.get(proof_chunk, set())
        true_positive += len(predicted & expected)
        false_positive += len(predicted - expected)
        false_negative += len(expected - predicted)

    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else None
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative
        else None
    )

    return {
        "n_gold": len(proofs),
        "attachment_accuracy": correct_attachments / len(proofs),
        "edge_precision": precision,
        "edge_recall": recall,
        "tp": true_positive,
        "fp": false_positive,
        "fn": false_negative,
    }
