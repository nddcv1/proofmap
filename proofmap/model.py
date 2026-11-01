from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any

SCHEMA_VERSION = 1


def _known_kwargs(cls: type, data: dict[str, Any]) -> dict[str, Any]:
    return {f.name: data[f.name] for f in fields(cls) if f.name in data}


@dataclass(eq=True)
class Evidence:
    quote: str
    char_start: int
    char_end: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Evidence":
        return cls(
            quote=data.get("quote", ""),
            char_start=int(data.get("char_start", 0)),
            char_end=int(data.get("char_end", 0)),
        )


@dataclass(eq=True)
class Node:
    id: str
    kind: str
    subkind: str
    label: str
    title: str
    aliases: list[str]
    book_id: str
    chapter: str
    section: str
    pdf_page: int
    printed_page: int
    statement: str
    display_name: str = ""
    source_chunks: list[str] = field(default_factory=list)
    proof: str = ""
    formula_review: bool = False
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Node":
        return cls(**_known_kwargs(cls, data))


@dataclass(eq=True)
class ProofAttachment:
    proof_chunk: str
    target_id: str
    target_kind: str
    method: str
    score: float
    margin: float
    status: str
    non_graph: bool
    evidence: str = ""
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProofAttachment":
        return cls(**_known_kwargs(cls, data))


@dataclass(eq=True)
class Edge:
    from_id: str
    to_id: str
    type: str
    confidence: str
    proof_chunk: str
    evidence: Evidence
    source: str
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "from": self.from_id,
            "to": self.to_id,
            "type": self.type,
            "confidence": self.confidence,
            "proof_chunk": self.proof_chunk,
            "evidence": self.evidence.to_dict(),
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Edge":
        evidence = data.get("evidence", {})
        if isinstance(evidence, dict):
            evidence = Evidence.from_dict(evidence)
        return cls(
            from_id=data.get("from", data.get("from_id", "")),
            to_id=data.get("to", data.get("to_id", "")),
            type=data.get("type", ""),
            confidence=data.get("confidence", ""),
            proof_chunk=data.get("proof_chunk", ""),
            evidence=evidence,
            source=data.get("source", ""),
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
        )
