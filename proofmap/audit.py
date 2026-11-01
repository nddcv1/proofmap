from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from proofmap.graph import isolated_nodes
from proofmap.model import Edge, Node, ProofAttachment


def _write(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _attachment_section(
    title: str, entries: list[ProofAttachment], lines: list[str]
) -> None:
    lines.append(f"## {title}")
    lines.append("")
    if not entries:
        lines.append("None.")
        lines.append("")
        return
    for entry in entries:
        lines.append(
            f"- `{entry.proof_chunk}` -> `{entry.target_id or '(none)'}` "
            f"({entry.target_kind or 'unknown'}) score={entry.score} "
            f"margin={entry.margin} {entry.evidence}"
        )
    lines.append("")


def write_audits(
    build_dir: str | Path,
    nodes: list[Node],
    attachments: list[ProofAttachment],
    edges: list[Edge],
    cycles: list[list[str]],
    edge_issues: list[dict[str, Any]] | None = None,
    node_issues: list[str] | None = None,
) -> None:
    build = Path(build_dir)
    build.mkdir(parents=True, exist_ok=True)
    edge_issues = edge_issues or []
    node_issues = node_issues or []

    by_status: dict[str, list[ProofAttachment]] = defaultdict(list)
    for attachment in attachments:
        by_status[attachment.status].append(attachment)

    lines = ["# Attachment audit", "", f"- total proofs: {len(attachments)}"]
    for status in sorted(by_status):
        lines.append(f"- {status}: {len(by_status[status])}")
    lines.append(
        f"- non-graph targets (example/exercise): "
        f"{sum(1 for item in attachments if item.non_graph)}"
    )
    lines.append("")
    _attachment_section("Ambiguous", by_status.get("ambiguous", []), lines)
    _attachment_section("Unresolved", by_status.get("unresolved", []), lines)
    _attachment_section("Detached", by_status.get("detached", []), lines)
    _write(build / "attachment_audit.md", lines)

    type_counts = Counter(edge.type for edge in edges)
    confidence_counts = Counter(edge.confidence for edge in edges)
    lines = [
        "# Edge audit",
        "",
        f"- total edges: {len(edges)}",
        "",
        "## By type",
        "",
    ]
    for key in sorted(type_counts):
        lines.append(f"- {key}: {type_counts[key]}")
    lines.extend(["", "## By confidence", ""])
    for key in sorted(confidence_counts):
        lines.append(f"- {key}: {confidence_counts[key]}")
    lines.extend(["", "## Extraction issues", ""])
    if edge_issues:
        for issue in edge_issues:
            lines.append(
                f"- {issue.get('type')} in `{issue.get('proof_chunk', '')}`: "
                f"{issue.get('text', '')}"
            )
    else:
        lines.append("None.")
    lines.extend(["", "## Cycles", ""])
    if cycles:
        for cycle in cycles:
            lines.append("- " + " -> ".join(cycle))
    else:
        lines.append("None.")
    lines.extend(["", "## Isolated nodes", ""])
    isolated = isolated_nodes(nodes, edges)
    if isolated:
        for node_id in isolated:
            lines.append(f"- `{node_id}`")
    else:
        lines.append("None.")
    zero_edge = [
        node.id
        for node in nodes
        if node.kind == "theorem"
        and not any(node.id in (edge.from_id, edge.to_id) for edge in edges)
    ]
    lines.extend(["", "## Zero-edge theorems", ""])
    if zero_edge:
        for node_id in sorted(zero_edge):
            lines.append(f"- `{node_id}`")
    else:
        lines.append("None.")
    _write(build / "edge_audit.md", lines)

    duplicate_labels: dict[tuple[str, str], int] = Counter(
        (node.book_id, node.label) for node in nodes if node.label
    )
    duplicates = [
        f"{book}:{label} appears {count} times"
        for (book, label), count in sorted(duplicate_labels.items())
        if count > 1
    ]
    lines = ["# Node audit", "", "## Parse warnings", ""]
    if node_issues:
        for issue in node_issues:
            lines.append(f"- {issue}")
    else:
        lines.append("None.")
    lines.extend(["", "## Duplicate labels", ""])
    if duplicates:
        for issue in duplicates:
            lines.append(f"- {issue}")
    else:
        lines.append("None.")
    _write(build / "node_audit.md", lines)
