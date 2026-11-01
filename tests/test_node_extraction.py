from proofmap.adapters.mathkb import extract_nodes


def chunk(cid, kind, text, section="§1.1 极限", chapter="第1章", book="demo"):
    return {
        "chunk_id": cid,
        "book_id": book,
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


def test_extracts_numbered_theorem_and_definition():
    chunks = [
        chunk("c1", "definition", "定义 1.1 设数列 $x_n$ 满足……"),
        chunk("c2", "theorem", "定理 1.2 收敛数列必有界。证明略。"),
    ]
    nodes, audit = extract_nodes(chunks)
    assert [n.id for n in nodes] == ["demo:定义1.1", "demo:定理1.2"]
    assert nodes[0].kind == "definition"
    assert nodes[1].subkind == "theorem"
    assert nodes[1].label == "定理 1.2"
    assert audit == []


def test_parses_named_parenthetical_and_subkind():
    chunks = [
        chunk("c1", "theorem", "引理(夹逼引理): 设……"),
        chunk("c2", "theorem", "推论 2.1 若……"),
    ]
    nodes, _ = extract_nodes(chunks)
    assert nodes[0].subkind == "lemma"
    assert nodes[0].title == "夹逼引理"
    assert nodes[1].subkind == "corollary"


def test_duplicate_numeric_labels_in_same_section_are_merged():
    chunks = [
        chunk("c1", "theorem", "定理 1.1 若 A 则 B。"),
        chunk("c2", "theorem", "定理 1.1 且若 B 则 C。"),
    ]
    nodes, audit = extract_nodes(chunks)
    assert len(nodes) == 1
    assert nodes[0].id == "demo:定理1.1"
    assert nodes[0].source_chunks == ["c1", "c2"]
    assert "若 A 则 B" in nodes[0].statement
    assert "若 B 则 C" in nodes[0].statement
    assert any("merged" in msg for msg in audit)


def test_prime_suffixed_labels_are_distinct():
    chunks = [
        chunk("c1", "theorem", "定理 1.1 第一版本。"),
        chunk("c2", "theorem", "定理 1.1′ 第二版本。"),
    ]
    nodes, audit = extract_nodes(chunks)
    assert len(nodes) == 2
    assert {node.label for node in nodes} == {"定理 1.1", "定理 1.1′"}
    assert nodes[0].id == "demo:定理1.1"
    assert nodes[1].id == "demo:定理1.1′"
    assert audit == []


def test_duplicate_numeric_labels_get_fallback_ids_and_audit():
    chunks = [
        chunk("c1", "theorem", "定理 1.1 第一处。"),
        chunk("c2", "theorem", "定理 1.1 第二处。", section="§1.2 另一节"),
    ]
    nodes, audit = extract_nodes(chunks)
    assert nodes[0].id != nodes[1].id
    assert nodes[0].id.startswith("demo:")
    assert any("duplicate numeric label" in msg for msg in audit)
