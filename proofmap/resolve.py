from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable

from proofmap.model import Node

_WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    return _WS_RE.sub("", text or "").casefold()


def _dedupe(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(items))


class NodeIndex:
    def __init__(
        self,
        nodes: list[Node],
        chunk_order: dict[str, int] | None = None,
    ) -> None:
        self.nodes = list(nodes)
        self.by_id = {node.id: node for node in self.nodes}
        self.label_index: dict[tuple[str, str], list[str]] = defaultdict(list)
        self.alias_index: dict[tuple[str, str], list[str]] = defaultdict(list)
        self.chunk_order = chunk_order or {}
        self.order: dict[str, int] = {}

        for position, node in enumerate(self.nodes):
            if node.source_chunks and node.source_chunks[0] in self.chunk_order:
                self.order[node.id] = self.chunk_order[node.source_chunks[0]]
            else:
                self.order[node.id] = position

            self.label_index[(node.book_id, normalize(node.label))].append(node.id)
            for alias in {node.label, node.title, *node.aliases}:
                key = normalize(alias)
                if key:
                    self.alias_index[(node.book_id, key)].append(node.id)

        for key, ids in list(self.label_index.items()):
            self.label_index[key] = _dedupe(ids)
        for key, ids in list(self.alias_index.items()):
            self.alias_index[key] = _dedupe(ids)

    def resolve_label(
        self, book_id: str, chapter: str, kind: str, number: str
    ) -> list[str]:
        ids = self.label_index.get((book_id, normalize(f"{kind}{number}")), [])
        if "." in number:
            return list(ids)
        return [
            node_id
            for node_id in ids
            if self.by_id[node_id].chapter == chapter
        ]

    def resolve_alias(self, book_id: str, chapter: str, alias: str) -> list[str]:
        ids = self.alias_index.get((book_id, normalize(alias)), [])
        scoped = [
            node_id
            for node_id in ids
            if self.by_id[node_id].chapter == chapter
        ]
        return scoped or list(ids)

    def aliases_for_book(self, book_id: str) -> dict[str, list[str]]:
        return {
            alias: ids
            for (alias_book, alias), ids in self.alias_index.items()
            if alias_book == book_id
        }

    def preceding(self, book_id: str, chapter: str, order: int) -> str | None:
        best: str | None = None
        best_order = -1
        for node in self.nodes:
            if node.book_id != book_id:
                continue
            if chapter and node.chapter != chapter:
                continue
            node_order = self.order.get(node.id, -1)
            if node_order < order and node_order > best_order:
                best = node.id
                best_order = node_order
        return best
