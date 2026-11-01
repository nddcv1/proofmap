from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
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
_PREFIX_RE = re.compile(
    r"^\s*(定义|定理|引理|推论|命题)\s*([0-9]+(?:\.[0-9]+)*[′'’*＊]*)?"
)
_PAREN_RE = re.compile(
    r"^\s*(?:定义|定理|引理|推论|命题)\s*(?:[0-9]+(?:\.[0-9]+)*[′'’*＊]*)?\s*[（(]([^）)]{1,40})[）)]"
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
        "paren_title": paren.group(1).strip() if paren else "",
        "aliases": aliases,
        "text": text,
    }


def _slug(text: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "_", text or "root").strip("_")
    return slug or "root"


def _make_node(chunk: dict[str, Any], info: dict[str, Any], node_id: str) -> Node:
    return Node(
        id=node_id,
        kind=info["kind"],
        subkind=info["subkind"],
        label=info["label"],
        title=info["title"],
        aliases=sorted(info["aliases"]),
        book_id=str(chunk.get("book_id", "")),
        chapter=str(chunk.get("chapter", "")),
        section=str(chunk.get("section", "")),
        pdf_page=int(chunk.get("pdf_page") or 0),
        printed_page=int(chunk.get("printed_page") or 0),
        statement=info["text"],
        source_chunks=[str(chunk.get("chunk_id", ""))],
        formula_review=bool(chunk.get("formula_review", False)),
    )


def _fallback_id(
    book_id: str,
    chunk: dict[str, Any],
    ordinals: Counter[tuple[str, str]],
) -> str:
    section_key = _slug(str(chunk.get("section") or chunk.get("chapter") or "root"))
    ordinals[(book_id, section_key)] += 1
    return f"{book_id}:{section_key}:{ordinals[(book_id, section_key)]:03d}"


def _merge_entries(
    entries: list[tuple[dict[str, Any], dict[str, Any]]],
    book_id: str,
    prefix: str,
    number: str,
) -> Node:
    first_chunk, first_info = entries[0]
    texts: list[str] = []
    aliases: set[str] = set()
    source_chunks: list[str] = []
    formula_review = False
    for chunk, info in entries:
        text = info["text"]
        if text not in texts:
            texts.append(text)
        aliases.update(info["aliases"])
        source_chunks.append(str(chunk.get("chunk_id", "")))
        formula_review = formula_review or bool(chunk.get("formula_review", False))

    title = first_info.get("paren_title") or first_info["title"]
    if not title or title == first_info["label"]:
        for _, info in entries[1:]:
            candidate = info.get("paren_title") or info["title"]
            if candidate and candidate != info["label"]:
                title = candidate
                break

    return Node(
        id=f"{book_id}:{prefix}{number}",
        kind=first_info["kind"],
        subkind=first_info["subkind"],
        label=first_info["label"],
        title=title,
        aliases=sorted(aliases),
        book_id=book_id,
        chapter=str(first_chunk.get("chapter", "")),
        section=str(first_chunk.get("section", "")),
        pdf_page=int(first_chunk.get("pdf_page") or 0),
        printed_page=int(first_chunk.get("printed_page") or 0),
        statement="\n\n".join(texts),
        source_chunks=source_chunks,
        formula_review=formula_review,
    )


def extract_nodes(chunks: list[dict[str, Any]]) -> tuple[list[Node], list[str]]:
    parsed: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for chunk in chunks:
        if chunk.get("kind") not in {"definition", "theorem"}:
            continue
        info = _parse_chunk(chunk)
        if info is None:
            continue
        parsed.append((chunk, info))

    groups: dict[tuple[str, str, str], list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for chunk, info in parsed:
        if info["number"]:
            key = (str(chunk.get("book_id", "")), info["prefix"], info["number"])
            groups[key].append((chunk, info))

    merged_keys: set[tuple[str, str, str]] = set()
    split_keys: set[tuple[str, str, str]] = set()
    for key, entries in groups.items():
        if len(entries) <= 1:
            continue
        scopes = {
            (str(chunk.get("chapter") or ""), str(chunk.get("section") or ""))
            for chunk, _ in entries
        }
        mergeable = len(scopes) == 1 and all(
            chapter and section for chapter, section in scopes
        )
        if mergeable:
            merged_keys.add(key)
        else:
            split_keys.add(key)

    audit: list[str] = []
    ordinals: Counter[tuple[str, str]] = Counter()
    nodes: list[Node] = []
    merged_done: set[tuple[str, str, str]] = set()
    split_audited: set[tuple[str, str, str]] = set()

    for chunk, info in parsed:
        book_id = str(chunk.get("book_id", ""))
        number = info["number"]
        key = (book_id, info["prefix"], number) if number else None

        if key is not None and key in merged_keys:
            if key in merged_done:
                continue
            merged_done.add(key)
            nodes.append(_merge_entries(groups[key], book_id, info["prefix"], number))
            audit.append(
                f"merged {len(groups[key])} chunks for duplicate numeric label "
                f"{info['prefix']} {number} in {book_id}"
            )
            continue

        if number and key in split_keys:
            if key not in split_audited:
                split_audited.add(key)
                audit.append(
                    f"duplicate numeric label {info['prefix']} {number} in "
                    f"{book_id} kept as separate nodes"
                )
            node_id = _fallback_id(book_id, chunk, ordinals)
        elif number:
            node_id = f"{book_id}:{info['prefix']}{number}"
        else:
            node_id = _fallback_id(book_id, chunk, ordinals)

        nodes.append(_make_node(chunk, info, node_id))

    return nodes, audit
