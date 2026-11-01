from __future__ import annotations

from proofmap.model import Evidence

_BOUNDARIES = set("。；;！？\n")


def make_evidence(
    text: str,
    start: int,
    end: int,
    context: int = 40,
    max_len: int = 160,
) -> Evidence:
    left = 0
    for index in range(start - 1, -1, -1):
        if text[index] in _BOUNDARIES:
            left = index + 1
            break

    right = len(text)
    for index in range(end, len(text)):
        if text[index] in _BOUNDARIES:
            right = index + 1
            break

    while left < start and text[left].isspace():
        left += 1
    while right > end and text[right - 1].isspace():
        right -= 1

    if right - left > max_len:
        lo = max(0, start - context)
        hi = min(len(text), end + context)
        if hi - lo > max_len:
            hi = lo + max_len
        left, right = lo, hi

    return Evidence(quote=text[left:right], char_start=left, char_end=right)
