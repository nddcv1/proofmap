from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from proofmap import __version__
from proofmap.build import build_all
from proofmap.evaluate import evaluate
from proofmap.io import read_json, read_jsonl
from proofmap.model import Edge, ProofAttachment
from proofmap.render import render_html


def _books(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _depth(value: str) -> int | None:
    if value == "all":
        return None
    depth = int(value)
    if depth < 1:
        raise argparse.ArgumentTypeError("depth must be >= 1 or 'all'")
    return depth


def _common() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="proofmap",
        description="Evidence-backed prerequisite graphs for math textbooks and notes.",
    )
    parser.add_argument("--version", action="version", version=f"proofmap {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", parents=[_common()], help="build graph artifacts")
    build.add_argument("--chunks", required=True, help="chunks.jsonl input")
    build.add_argument("--out", required=True, help="output directory")
    build.add_argument("--book", type=_books, default=None, help="comma-separated book ids")
    build.add_argument("--include-ambiguous", action="store_true")
    build.add_argument("--corrections", default=None, help="corrections.yaml")

    audit = subparsers.add_parser("audit", parents=[_common()], help="summarize audits")
    audit.add_argument("--build", default="build")

    render = subparsers.add_parser("render", parents=[_common()], help="write single-file HTML")
    render.add_argument("--build", default="build")
    render.add_argument("--out", required=True)
    render.add_argument("--title", default="ProofMap · 数学教材先修地图")

    query = subparsers.add_parser("query", parents=[_common()], help="traverse the graph")
    query.add_argument("kind", choices=["prereq", "dependents"])
    query.add_argument("node")
    query.add_argument("--build", default="build")
    query.add_argument("--depth", type=_depth, default=None)
    query.add_argument("--include-concepts", action="store_true")

    evaluate_parser = subparsers.add_parser(
        "eval", parents=[_common()], help="evaluate against a gold set"
    )
    evaluate_parser.add_argument("--build", default="build")
    evaluate_parser.add_argument("--gold", required=True)
    evaluate_parser.add_argument("--min-precision", type=float, default=0.95)
    evaluate_parser.add_argument("--min-recall", type=float, default=0.0)
    return parser


def _load_graph(build_dir: str | Path) -> dict[str, Any]:
    path = Path(build_dir) / "graph.json"
    if not path.exists():
        raise FileNotFoundError(f"graph not found: {path}")
    return read_json(path)


def _query(args: argparse.Namespace) -> int:
    graph = _load_graph(args.build)
    nodes = {node["id"]: node for node in graph.get("nodes", [])}
    if args.node not in nodes:
        print(f"node not found: {args.node}", file=sys.stderr)
        return 1

    edges = graph.get("edges", [])

    def display(node_id: str) -> str:
        node = nodes.get(node_id, {})
        label = node.get("label") or node_id
        title = node.get("title") or ""
        if title and title != label and title not in label:
            return f"{label} · {title}"
        return label

    node_label = {node_id: display(node_id) for node_id in nodes}
    visited = {args.node}
    queue: list[tuple[str, int]] = [(args.node, 0)]
    results: list[dict[str, Any]] = []

    while queue:
        current, depth = queue.pop(0)
        if args.depth is not None and depth >= args.depth:
            continue
        for edge in edges:
            if edge.get("type") == "definition_term" and not args.include_concepts:
                continue
            if args.kind == "prereq" and edge.get("to") == current:
                neighbour = edge.get("from")
            elif args.kind == "dependents" and edge.get("from") == current:
                neighbour = edge.get("to")
            else:
                continue
            if not neighbour or neighbour in visited:
                continue
            visited.add(neighbour)
            results.append(
                {
                    "id": neighbour,
                    "label": node_label.get(neighbour, neighbour),
                    "depth": depth + 1,
                    "type": edge.get("type", ""),
                    "confidence": edge.get("confidence", ""),
                    "quote": (edge.get("evidence") or {}).get("quote", ""),
                    "proof_chunk": edge.get("proof_chunk", ""),
                }
            )
            queue.append((neighbour, depth + 1))

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif not results:
        print("没有找到依赖。")
    else:
        for item in results:
            indent = "  " * (item["depth"] - 1)
            print(
                f"{indent}- {item['label']} [{item['type']}] "
                f"({item['id']})"
            )
    return 0


def _eval(args: argparse.Namespace) -> int:
    build_dir = Path(args.build)
    attachments = read_jsonl(build_dir / "attachments.jsonl", ProofAttachment)
    edges = read_jsonl(build_dir / "edges.jsonl", Edge)
    gold_path = Path(args.gold)
    if not gold_path.exists():
        raise FileNotFoundError(f"gold set not found: {gold_path}")
    gold = yaml.safe_load(gold_path.read_text(encoding="utf-8")) or {}
    result = evaluate(attachments, edges, gold)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"gold proofs: {result['n_gold']}")
        for key in ("attachment_accuracy", "edge_precision", "edge_recall"):
            value = result[key]
            print(f"{key.replace('_', ' ')}: {'n/a' if value is None else f'{value:.3f}'}")
        print(f"tp={result['tp']} fp={result['fp']} fn={result['fn']}")

    if result["n_gold"] == 0:
        return 0
    precision = result["edge_precision"]
    recall = result["edge_recall"]
    failed = False
    if precision is not None and precision < args.min_precision:
        print(
            f"precision {precision:.3f} below threshold {args.min_precision:.3f}",
            file=sys.stderr,
        )
        failed = True
    if recall is not None and recall < args.min_recall:
        print(
            f"recall {recall:.3f} below threshold {args.min_recall:.3f}",
            file=sys.stderr,
        )
        failed = True
    return 3 if failed else 0


def _audit(args: argparse.Namespace) -> int:
    graph = _load_graph(args.build)
    metadata = graph.get("metadata", {})
    if args.json:
        print(json.dumps(metadata, ensure_ascii=False, indent=2))
        return 0
    counts = metadata.get("counts", {})
    print(f"nodes: {counts.get('nodes', {}).get('total', 0)}")
    print(f"edges: {counts.get('edges', {}).get('total', 0)}")
    print(f"attachments: {counts.get('attachments', {}).get('by_status', {})}")
    print(f"cycles: {len(metadata.get('cycles', []))}")
    build = Path(args.build)
    for name in ("attachment_audit.md", "edge_audit.md", "node_audit.md"):
        path = build / name
        if path.exists():
            print(f"report: {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            summary = build_all(
                chunks_path=args.chunks,
                out_dir=args.out,
                books=args.book,
                include_ambiguous=args.include_ambiguous,
                corrections_path=args.corrections,
            )
            if args.json:
                print(json.dumps(summary, ensure_ascii=False, indent=2))
            else:
                print(f"nodes: {summary['nodes']}")
                print(f"edges: {summary['edges']}")
                print(f"attachments: {summary['attachments']}")
                print(f"cycles: {summary['cycles']}")
                print(f"edge issues: {summary['edge_issues']}")
                print(f"build: {summary['build_dir']}")
            return 0
        if args.command == "audit":
            return _audit(args)
        if args.command == "render":
            graph = _load_graph(args.build)
            render_html(graph, args.out, title=args.title)
            size = Path(args.out).stat().st_size
            if args.json:
                print(json.dumps({"out": args.out, "bytes": size}, ensure_ascii=False))
            else:
                print(f"wrote {args.out} ({size} bytes)")
            return 0
        if args.command == "query":
            return _query(args)
        if args.command == "eval":
            return _eval(args)
    except (FileNotFoundError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"proofmap: error: {exc}", file=sys.stderr)
        return 1
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
