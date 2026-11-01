from __future__ import annotations

from proofmap.model import Evidence


def make_evidence(text: str, start: int, end: int, context: int = 40) -> Evidence:
    lo = max(0, start - context)
    hi = min(len(text), end + context)
    return Evidence(quote=text[lo:hi], char_start=lo, char_end=hi)
