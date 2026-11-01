from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def write_jsonl(path: str | Path, items: Iterable[Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as fh:
        for item in items:
            payload = item.to_dict() if hasattr(item, "to_dict") else item
            fh.write(canonical_json(payload) + "\n")


def read_jsonl(path: str | Path, cls: type) -> list[Any]:
    source = Path(path)
    with source.open("r", encoding="utf-8") as fh:
        return [cls.from_dict(json.loads(line)) for line in fh if line.strip()]


def write_json(path: str | Path, data: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(canonical_json(data) + "\n", encoding="utf-8")


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
