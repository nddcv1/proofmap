"""Generate the synthetic demo corpus.

The demo is authored for this repository. It contains no textbook text.
Run: python examples/demo/build_demo.py
"""

from __future__ import annotations

import json
from pathlib import Path

BOOK = {
    "book_id": "demo",
    "book_title": "极小分析讲义",
    "short": "极小",
    "subject": "数学分析",
}

CHAPTER_1 = "第 1 章 数列极限"
CHAPTER_2 = "第 2 章 微分中值定理"
SECTION_1_1 = "§ 1.1 数列极限与有界性"
SECTION_1_2 = "§ 1.2 单调数列"
SECTION_2_1 = "§ 2.1 Rolle 定理"

CHUNKS: list[tuple[str, str, str, str]] = [
    (
        "definition",
        "定义 1.1（数列极限）设 $\\{x_n\\}$ 是数列，$a\\in\\mathbb{R}$。若对任意 $\\varepsilon>0$，存在正整数 $N$，当 $n>N$ 时 $|x_n-a|<\\varepsilon$，则称 $\\{x_n\\}$ 收敛于 $a$。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "definition",
        "定义 1.2（有界数列）若存在 $M>0$，使得对一切正整数 $n$ 有 $|x_n|\\le M$，则称 $\\{x_n\\}$ 有界。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "theorem",
        "定理 1.1（极限唯一性）若数列 $\\{x_n\\}$ 收敛，则它的极限唯一。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "text",
        "分析：证明要用反证法，并两次使用数列极限的定义。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "proof",
        "证明：设 $x_n\\to a$ 且 $x_n\\to b$。由数列极限的定义，对任意 $\\varepsilon>0$，存在 $N_1,N_2$，当 $n>\\max(N_1,N_2)$ 时同时有 $|x_n-a|<\\varepsilon/2$ 与 $|x_n-b|<\\varepsilon/2$。于是 $|a-b|<\\varepsilon$，故 $a=b$。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "theorem",
        "定理 1.2（收敛数列有界）收敛数列必有界。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "proof",
        "证明：设 $x_n\\to a$。由定义 1.1，取 $\\varepsilon=1$，存在 $N$，当 $n>N$ 时 $|x_n|<|a|+1$。再根据有界数列的定义，$\\{x_n\\}$ 有界。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "example",
        "例 1 证明 $\\lim_{n\\to\\infty}\\frac{1}{n}=0$。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "proof",
        "证明：由定义 1.1，对任意 $\\varepsilon>0$，取 $N=\\lceil 1/\\varepsilon\\rceil$，当 $n>N$ 时 $\\left|\\frac{1}{n}-0\\right|<\\varepsilon$。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "theorem",
        "定理 1.3（夹逼定理）若 $a_n\\le b_n\\le c_n$，且 $a_n\\to L$、$c_n\\to L$，则 $b_n\\to L$。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "proof",
        "证明：由定义 1.1，对任意 $\\varepsilon>0$，存在 $N$，当 $n>N$ 时 $L-\\varepsilon<a_n$ 且 $c_n<L+\\varepsilon$。由 $a_n\\le b_n\\le c_n$ 得 $L-\\varepsilon<b_n<L+\\varepsilon$，故 $b_n\\to L$。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "theorem",
        "引理 1.1（子列收敛）若 $x_n\\to a$，则对任意子列 $x_{n_k}$，都有 $x_{n_k}\\to a$。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "proof",
        "证明：由定义 1.1，对任意 $\\varepsilon>0$，存在 $N$，当 $n>N$ 时 $|x_n-a|<\\varepsilon$。取 $K$ 使 $n_K>N$，则当 $k>K$ 时 $|x_{n_k}-a|<\\varepsilon$。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "theorem",
        "推论 1.1 收敛数列的任意子列都有界。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "proof",
        "证明：由定理 1.2 可知，收敛数列有界；子列是数列，故其有界。",
        CHAPTER_1,
        SECTION_1_1,
    ),
    (
        "definition",
        "定义 1.3（单调数列）若 $x_1\\le x_2\\le\\cdots$，则称 $\\{x_n\\}$ 单调递增。",
        CHAPTER_1,
        SECTION_1_2,
    ),
    (
        "theorem",
        "定理 1.4（单调有界定理）单调有界数列必有极限。",
        CHAPTER_1,
        SECTION_1_2,
    ),
    (
        "proof",
        "证明：设 $\\{x_n\\}$ 是有界数列且是单调数列。由定义 1.3，它单调递增。由定义 1.2，它有上界。由确界原理，它有上确界 $a$，再按定义 1.1 验证 $x_n\\to a$。",
        CHAPTER_1,
        SECTION_1_2,
    ),
    (
        "theorem",
        "定理 2.1（Rolle 定理）若函数 $f$ 在 $[a,b]$ 上连续、在 $(a,b)$ 内可导，且 $f(a)=f(b)$，则存在 $\\xi\\in(a,b)$ 使 $f'(\\xi)=0$。",
        CHAPTER_2,
        SECTION_2_1,
    ),
    (
        "theorem",
        "定理 2.2（Rolle 定理的应用）若 $f$ 在 $[a,b]$ 上满足 Rolle 定理的条件，则存在 $\\xi\\in(a,b)$ 使 $f'(\\xi)=0$。",
        CHAPTER_2,
        SECTION_2_1,
    ),
    (
        "proof",
        "证明：由 Rolle 定理可知，存在 $\\xi\\in(a,b)$ 使 $f'(\\xi)=0$。",
        CHAPTER_2,
        SECTION_2_1,
    ),
    (
        "theorem",
        "定理 2.3（直接推论）若 $f$ 在 $[a,b]$ 上满足定理 2.2 的条件，则存在驻点。",
        CHAPTER_2,
        SECTION_2_1,
    ),
    (
        "proof",
        "证明：由上述定理可知存在 $\\xi$ 使 $f'(\\xi)=0$，即 $\\xi$ 为驻点。",
        CHAPTER_2,
        SECTION_2_1,
    ),
]


def build() -> Path:
    out = Path(__file__).with_name("chunks.jsonl")
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        for index, (kind, text, chapter, section) in enumerate(CHUNKS, start=1):
            payload = {
                "chunk_id": f"demo-p{index:04d}-{index:04d}",
                **BOOK,
                "pdf_page": index,
                "printed_page": index,
                "chapter": chapter,
                "section": section,
                "subsection": "",
                "kind": kind,
                "text": text,
                "plain_text": text,
                "source_image": "",
                "formula_review": False,
            }
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return out


if __name__ == "__main__":
    print(build())
