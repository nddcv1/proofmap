from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from proofmap.model import Node

_PREFIXES = {
    "定义": "definition",
    "定理": "theorem",
    "引理": "lemma",
    "推论": "corollary",
    "命题": "proposition",
}
_PREFIX_RE = re.compile(r"^\s*(定义|定理|引理|推论|命题)\s*([0-9]+(?:\.[0-9]+)*)?")
_PAREN_RE = re.compile(
    r"^\s*(?:定义|定理|引理|推论|命题)\s*(?:[0-9]+(?:\.[0-9]+)*)?\s*[（(]([^）)]{1,40})[）)]"
)
_SENTENCE_RE = re.compile(r"[。；;]")
_NAMED_SECTION_MARKERS = ("定理", "引理", "推论", "命题", "公式", "不等式")


def load_chunks(path: str | Path) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def _parse_chunk(chunk: dict[str, Any]) -> dict[str, Any] | None:
    text = str(chunk.get("text", "")).strip()
    match = _PREFIX_RE.match(text)
    if not match:
        return None

    prefix, number = match.group(1), match.group(2) or ""
    subkind = _PREFIXES[prefix]
    kind = "definition" if subkind == "definition" else "theorem"
    label = f"{prefix} {number}".strip()

    title = ""
    paren = _PAREN_RE.match(text)
    if paren:
        title = paren.group(1).strip()
    if not title:
        rest = text[match.end() :].lstrip(" :：")
        stop = _SENTENCE_RE.search(rest)
        if stop:
            rest = rest[: stop.start()]
        title = rest.strip()[:40]
    if not title:
        title = label

    aliases = {label, label.replace(" ", "")}
    if title and title != label:
        aliases.add(title)
    if paren:
        aliases.add(paren.group(1).strip())
    for field in ("section", "subsection"):
        section = str(chunk.get(field) or "").strip()
        if section and any(marker in section for marker in _NAMED_SECTION_MARKERS):
            aliases.add(section)

    return {
        "prefix": prefix,
        "number": number,
        "kind": kind,
        "subkind": subkind,
        "label": label,
        "title": title,
        "aliases": aliases,
        "text": text,
    }


def _slug(text: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "_", text or "root").strip("_")
    return slug or "root"


def extract_nodes(chunks: list[dict[str, Any]]) -> tuple[list[Node], list[str]]:
    parsed: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for chunk in chunks:
        if chunk.get("kind") not in {"definition", "theorem"}:
            continue
        info = _parse_chunk(chunk)
        if info is None:
            continue
        parsed.append((chunk, info))

    numeric_counts: Counter[tuple[str, str, str]] = Counter()
    for chunk, info in parsed:
        if info["number"]:
            key = (str(chunk.get("book_id", "")), info["prefix"], info["number"])
            numeric_counts[key] += 1

    audit: list[str] = []
    ordinals: Counter[tuple[str, str]] = Counter()
    nodes: list[Node] = []

    for chunk, info in parsed:
        book_id = str(chunk.get("book_id", ""))
        number = info["number"]
        unique_numeric = bool(number) and numeric_counts[
            (book_id, info["prefix"], number)
        ] == 1

        if unique_numeric:
            node_id = f"{book_id}:{info['prefix']}{number}"
        else:
            section_key = _slug(
                str(chunk.get("section") or chunk.get("chapter") or "root")
            )
            ordinals[(book_id, section_key)] += 1
            node_id = f"{book_id}:{section_key}:{ordinals[(book_id, section_key)]:03d}"
            if number:
                duplicate_key = (book_id, info["prefix"], number)
                if numeric_counts[duplicate_key] > 1:
                    audit.append(
                        "duplicate numeric label "
                        f"{info['prefix']} {number} in {book_id}"
                    )

        node = Node(
            id=node_id,
            kind=info["kind"],
            subkind=info["subkind"],
            label=info["label"],
            title=info["title"],
            aliases=sorted(info["aliases"]),
            book_id=book_id,
            chapter=str(chunk.get("chapter", "")),
            section=str(chunk.get("section", "")),
            pdf_page=int(chunk.get("pdf_page") or 0),
            printed_page=int(chunk.get("printed_page") or 0),
            statement=info["text"],
            source_chunks=[str(chunk.get("chunk_id", ""))],
            formula_review=bool(chunk.get("formula_review", False)),
        )
        nodes.append(node)

    return nodes, audit
