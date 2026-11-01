from __future__ import annotations

import html as html_lib
import json
from pathlib import Path
from typing import Any

_TEMPLATE = Path(__file__).with_name("template.html")
_VENDOR = Path(__file__).with_name("vendor")


def render_html(
    graph: dict[str, Any],
    out_path: str | Path,
    title: str = "ProofMap · 数学教材先修地图",
) -> None:
    template = _TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(graph, ensure_ascii=False, sort_keys=True).replace(
        "</", "<\\/"
    )
    replacements = {
        "__TITLE__": html_lib.escape(title),
        "__CYTOSCAPE_JS__": (_VENDOR / "cytoscape.min.js").read_text(encoding="utf-8"),
        "__DAGRE_JS__": (_VENDOR / "dagre.min.js").read_text(encoding="utf-8"),
        "__CY_DAGRE_JS__": (_VENDOR / "cytoscape-dagre.js").read_text(encoding="utf-8"),
        "__GRAPH_JSON__": payload,
    }
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)

    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template, encoding="utf-8")
