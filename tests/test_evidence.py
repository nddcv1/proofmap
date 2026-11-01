from proofmap.extract.evidence import make_evidence


def test_evidence_prefers_the_matching_sentence():
    text = "第一句。由定理 1.1 可知。第二句。"
    start = text.index("定理")
    evidence = make_evidence(text, start, start + 4)
    assert evidence.quote == "由定理 1.1 可知。"
    assert text[evidence.char_start : evidence.char_end] == evidence.quote


def test_evidence_caps_very_long_sentences():
    text = "前" * 100 + "由定理 1.1 可知" + "后" * 100
    start = text.index("定理")
    evidence = make_evidence(text, start, start + 4, context=10, max_len=60)
    assert len(evidence.quote) <= 60
    assert "定理 1.1" in evidence.quote
