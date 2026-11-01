import json
from pathlib import Path

from proofmap.io import canonical_json, read_jsonl, write_jsonl
from proofmap.model import Evidence


def test_jsonl_utf8_roundtrip(tmp_path: Path):
    path = tmp_path / "edges.jsonl"
    items = [Evidence("由定理 1.1 可知", 0, 6)]
    write_jsonl(path, items)
    raw = path.read_text(encoding="utf-8")
    assert "由定理" in raw
    assert read_jsonl(path, Evidence) == items


def test_canonical_json_is_stable():
    assert canonical_json({"b": 1, "a": 2}) == '{"a": 2, "b": 1}'
    json.loads(canonical_json({"x": "中文"}))
