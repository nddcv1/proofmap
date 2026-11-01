from proofmap.evaluate import evaluate
from proofmap.model import Edge, Evidence, ProofAttachment


def test_precision_recall_and_attachment_accuracy():
    attachments = [
        ProofAttachment(
            proof_chunk="p1",
            target_id="b:定理1.1",
            target_kind="theorem",
            method="proximity",
            score=0.9,
            margin=0.3,
            status="attached",
            non_graph=False,
            evidence="",
        )
    ]
    edges = [
        Edge(
            from_id="b:定义1.1",
            to_id="b:定理1.1",
            type="definition_term",
            confidence="inferred",
            proof_chunk="p1",
            evidence=Evidence("一致连续", 0, 4),
            source="rule",
        )
    ]
    gold = {
        "proofs": [
            {
                "proof_chunk": "p1",
                "target_id": "b:定理1.1",
                "used": ["b:定义1.1", "b:定理1.0"],
            }
        ]
    }
    result = evaluate(attachments, edges, gold)
    assert result["attachment_accuracy"] == 1.0
    assert result["edge_precision"] == 1.0
    assert result["edge_recall"] == 0.5
    assert result["n_gold"] == 1


def test_empty_gold_returns_none_metrics():
    result = evaluate([], [], {"proofs": []})
    assert result["attachment_accuracy"] is None
    assert result["edge_precision"] is None
    assert result["edge_recall"] is None
