from proofmap.adapters.mathkb import extract_nodes
from proofmap.attach import apply_attachments, attach_proofs


def chunk(cid, kind, text, section="§1.1 极限", chapter="第1章"):
    return {
        "chunk_id": cid,
        "book_id": "demo",
        "book_title": "Demo",
        "short": "Demo",
        "subject": "数学分析",
        "pdf_page": 1,
        "printed_page": 1,
        "chapter": chapter,
        "section": section,
        "subsection": "",
        "kind": kind,
        "text": text,
        "plain_text": text,
        "source_image": "",
        "formula_review": False,
    }


def test_proof_attaches_to_preceding_theorem():
    chunks = [
        chunk("c1", "theorem", "定理 1.1 若 A 则 B。"),
        chunk("c2", "proof", "证明: 由定义可知 B 成立。"),
    ]
    nodes, _ = extract_nodes(chunks)
    attachments = attach_proofs(chunks, nodes)
    assert len(attachments) == 1
    assert attachments[0].target_id == "demo:定理1.1"
    assert attachments[0].status == "attached"
    assert attachments[0].non_graph is False


def test_example_proof_is_non_graph():
    chunks = [
        chunk("c1", "example", "例 1 求极限。"),
        chunk("c2", "proof", "证明: 直接计算。"),
    ]
    nodes, _ = extract_nodes(chunks)
    attachments = attach_proofs(chunks, nodes)
    assert attachments[0].target_kind == "example"
    assert attachments[0].non_graph is True
    assert attachments[0].target_id == "demo:example:c1"


def test_unresolved_when_no_candidate():
    chunks = [chunk("c1", "proof", "证明: 显然。")]
    nodes, _ = extract_nodes(chunks)
    attachments = attach_proofs(chunks, nodes)
    assert attachments[0].status == "unresolved"
    assert attachments[0].target_id == ""


def test_close_scores_are_ambiguous():
    chunks = [
        chunk("c1", "theorem", "定理 1.1 甲。"),
        chunk("c2", "theorem", "定理 1.2 乙。"),
        chunk("c3", "proof", "证明: 由甲可知。"),
    ]
    nodes, _ = extract_nodes(chunks)
    attachments = attach_proofs(chunks, nodes)
    assert attachments[0].status == "ambiguous"


def test_inline_proof_penalty_prevents_attachment():
    chunks = [
        chunk("c1", "theorem", "定理 1.1 若 A 则 B。证明: 略。"),
        chunk("c2", "proof", "证明: 重复证明。"),
    ]
    nodes, _ = extract_nodes(chunks)
    attachments = attach_proofs(chunks, nodes)
    assert attachments[0].status != "attached"


def test_empty_section_fallback_is_ambiguous():
    chunks = [
        chunk("c1", "theorem", "定理 1.1 若 A 则 B。", section=""),
        chunk("c2", "proof", "证明: 由定义可知。", section=""),
    ]
    nodes, _ = extract_nodes(chunks)
    attachments = attach_proofs(chunks, nodes)
    assert attachments[0].status == "ambiguous"


def test_example_statement_containing_prove_word_is_not_inline_penalty():
    chunks = [
        chunk("c1", "example", "例 1 证明极限存在。"),
        chunk("c2", "proof", "证明: 由定义可知。"),
    ]
    nodes, _ = extract_nodes(chunks)
    attachments = attach_proofs(chunks, nodes)
    assert attachments[0].status == "attached"
    assert attachments[0].non_graph is True


def test_apply_attachments_is_idempotent():
    chunks = [
        chunk("c1", "theorem", "定理 1.1 若 A 则 B。"),
        chunk("c2", "proof", "证明: 由定义可知。"),
    ]
    nodes, _ = extract_nodes(chunks)
    attachments = attach_proofs(chunks, nodes)
    apply_attachments(nodes, attachments, chunks)
    first = nodes[0].proof
    apply_attachments(nodes, attachments, chunks)
    assert nodes[0].proof == first
    assert "由定义可知" in first
