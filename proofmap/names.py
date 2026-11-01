from __future__ import annotations

import re
from collections import Counter
from typing import Any

from proofmap.model import Node

GENERIC_LABELS = {"定义", "定理", "引理", "推论", "命题"}
MATH_RE = re.compile(r"\$\$[\s\S]*?\$\$|\$[^$]*\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)")

# Strong statement patterns are checked before a short title: a few OCR chunk
# titles carry the name of a neighboring theorem, so the statement wins.
_STRONG: list[tuple[str, str]] = [
    (r"Newton.*迭代|迭代.*Newton", "Newton 迭代收敛定理"),
    (r"添加括号|加括号|结合律", "收敛级数的括号结合律"),
    (r"条件收敛.*更序|更序.*条件收敛|Riemann.*更序|更序.*Riemann", "Riemann 重排定理"),
    (r"f\s*\(\s*a\s*\)\s*\\cdot\s*f\s*\(\s*b\s*\)\s*<\s*0", "零点定理"),
    (r"f'\(x\)\s*\\equiv\s*0|导数.*恒为零", "导数恒为零的判定"),
    (r"F\s*\^\s*\{\s*\\prime\s*\}\s*\(y\)|F\s*'\s*\(y\)|含参变量.*(可导|求导|导数)", "含参变量积分的求导法则"),
    (r"与路径无关|原函数.*P\s*d\s*x.*Q\s*d\s*y", "曲线积分与路径无关的条件"),
    (r"d'Alembert.*Cauchy|Cauchy.*d'Alembert", "Cauchy 与 d'Alembert 判别法的关系"),
]

# Specific theorem names first. Do not add broad chapter topics here: a broad
# name repeated for every theorem is worse than a section topic + number.
_CURATED: list[tuple[str, str]] = [
    (r"上确界.*下确界|max\s*E|min\s*E", "上/下确界的可达性"),
    (r"上极限.*(等价|刻画)|最大极限点|最小极限点", "上极限与下极限的等价刻画"),
    (r"varlimsup|上极限.*下极限.*充分必要|充分必要.*上极限", "上极限与下极限的收敛准则"),
    (r"\\varlimsup.*x_n\s*\+\s*y_n|上极限.*(加法|次可加)", "上极限的次可加性"),
    (r"\\varlimsup.*x_n\s*y_n|上极限.*(乘积|乘)", "上极限的乘积性质"),
    (r"绝对收敛.*x_\{?n\}?\s*\^\s*\{?\+|条件收敛.*x_\{?n\}?\s*\^\s*\{?\+|正部|负部", "绝对收敛与条件收敛的分解"),
    (r"更序.*绝对收敛|绝对收敛.*更序", "绝对收敛级数的更序不变性"),
    (r"绝对收敛.*(乘积|乘)|乘积.*绝对收敛", "绝对收敛级数的乘积"),
    (r"无穷乘积.*必要", "无穷乘积收敛的必要条件"),
    (r"无穷乘积.*(ln|对数)|对数.*无穷乘积", "无穷乘积与对数级数的等价性"),
    (r"无穷乘积.*绝对收敛|绝对收敛.*无穷乘积", "无穷乘积的绝对收敛性"),
    (r"无穷乘积.*充分必要|充分必要.*无穷乘积", "无穷乘积与级数的等价性"),
    (r"\\alpha\s*x_\{?n\}?.*\\beta\s*y_\{?n\}?", "数列极限的运算性质"),
    (r"\\alpha\s*f\s*\(x\)\s*\+\s*\\beta\s*g\s*\(x\)", "函数极限的运算性质"),
    (r"g.*leqslant.*f.*leqslant.*h", "函数极限的夹逼定理"),
    (r"A\s*\\neq\s*0", "函数极限的局部保号性"),
    (r"lim.*=A.*lim.*=B.*(A\s*>\s*B|g\(x\)\\leqslant f\(x\)|g\(x\)\\geqslant f\(x\))", "函数极限的保序性"),
    (r"lim.*存在.*充分必要.*数列|函数值数列|对于任意满足条件.*x_\{n\}", "函数极限的序列式判别法"),
    (r"都是.*极限.*则.*A\s*=\s*B|A\s*与\s*B\s*都是.*极限", "函数极限的唯一性"),
    (r"可求面积|边界.*面积", "可求面积的条件"),
    (r"异号|f\s*\(\s*a\s*\)\s*f\s*\(\s*b\s*\)\s*<\s*0", "零点定理"),
    (r"幂级数.*展开|展开.*幂级数", "幂级数展开定理"),
    (r"Rolle", "Rolle 定理"),
    (r"Lagrange.*中值|中值.*Lagrange", "Lagrange 中值定理"),
    (r"Cauchy.*中值|中值.*Cauchy", "Cauchy 中值定理"),
    (r"Cauchy.*(收敛|准则|原理)|(收敛|准则|原理).*Cauchy", "Cauchy 收敛原理"),
    (r"Taylor", "Taylor 公式"),
    (r"Peano", "Peano 余项"),
    (r"Leibniz.*判别|判别.*Leibniz", "Leibniz 判别法"),
    (r"Leibniz", "Leibniz 公式"),
    (r"Fermat", "Fermat 引理"),
    (r"Darboux", "Darboux 定理"),
    (r"Stolz", "Stolz 定理"),
    (r"Bolzano[- ]?Weierstrass", "Bolzano-Weierstrass 定理"),
    (r"Heine[- ]?Borel", "Heine-Borel 定理"),
    (r"Heine", "Heine 定理"),
    (r"Cantor", "Cantor 定理"),
    (r"Dedekind", "Dedekind 切割定理"),
    (r"Weierstrass.*判别|判别.*Weierstrass", "Weierstrass 判别法"),
    (r"Weierstrass", "Weierstrass 定理"),
    (r"Green", "Green 公式"),
    (r"Gauss", "Gauss 公式"),
    (r"Stokes", "Stokes 公式"),
    (r"Abel", "Abel 判别法"),
    (r"Dirichlet", "Dirichlet 判别法"),
    (r"L.?Hospital|洛必达", "L'Hospital 法则"),
    (r"单调有界.*数列|数列.*单调有界|单调有界.*收敛", "单调有界定理"),
    (r"闭区间套", "闭区间套定理"),
    (r"确界.*(唯|惟)一|(唯|惟)一.*确界|确界存在", "确界存在定理"),
    (r"夹逼", "夹逼定理"),
    (r"比较判别", "比较判别法"),
    (r"比值判别|达朗贝尔", "比值判别法"),
    (r"根值判别|柯西判别", "根值判别法"),
    (r"积分判别", "积分判别法"),
    (r"一致收敛.*Cauchy|Cauchy.*一致收敛", "一致收敛的 Cauchy 准则"),
    (r"逐项求导", "逐项求导定理"),
    (r"逐项积分", "逐项积分定理"),
    (r"微积分基本", "微积分基本定理"),
    (r"积分中值", "积分中值定理"),
    (r"换元", "换元积分法"),
    (r"分部积分", "分部积分法"),
    (r"无穷小.*比较|等价无穷小|无穷小.*阶", "无穷小比较"),
    (r"无穷大量", "无穷大量的性质"),
    (r"子列.*收敛|收敛.*子列", "子列收敛性"),
    (r"无界.*子列|子列.*无界", "无界数列的子列性质"),
    (r"均收敛.*a\s*<\s*b|a\s*<\s*b.*均收敛", "收敛数列的保序性"),
    (r"极限.*(唯|惟)一|(唯|惟)一.*极限", "极限唯一性"),
    (r"保号", "极限的保号性"),
    (r"保序", "极限的保序性"),
    (r"四则.*极限|极限.*四则", "极限的运算性质"),
    (r"四则.*导数|导数.*四则", "导数四则运算"),
    (r"函数极限.*(存在|有限).*充分必要|函数极限.*Cauchy", "函数极限的 Cauchy 准则"),
    (r"闭区间.*连续.*有界|有界.*闭区间.*连续", "有界性定理"),
    (r"闭区间.*连续.*(最大|最小)|(最大|最小).*闭区间.*连续", "最值定理"),
    (r"介值", "介值定理"),
    (r"零点", "零点定理"),
    (r"一致连续", "一致连续性"),
    (r"偏导数.*连续.*可微|可微.*偏导数.*连续", "可微的充分条件"),
    (r"混合偏导.*(相等|连续)", "Clairaut 定理"),
    (r"可微.*可导|可导.*可微", "可微与可导等价"),
    (r"反函数.*导|导.*反函数", "反函数求导法则"),
    (r"复合函数.*连续", "复合函数的连续性"),
    (r"初等函数.*连续", "初等函数的连续性"),
    (r"极值.*第一|第一.*极值", "极值第一充分条件"),
    (r"极值.*第二|第二.*极值", "极值第二充分条件"),
    (r"极值.*(充分|必要)", "极值判定定理"),
    (r"隐函数", "隐函数定理"),
    (r"连续.*可积|可积.*连续", "连续函数的可积性"),
    (r"可积.*条件", "可积条件"),
    (r"大和|小和|达布", "达布和性质"),
    (r"交错级数", "Leibniz 判别法"),
    (r"绝对收敛", "绝对收敛性"),
    (r"条件收敛", "条件收敛性"),
    (r"收敛半径", "幂级数收敛半径"),
    (r"变限积分", "变限积分求导"),
    (r"弧长", "弧长公式"),
    (r"旋转体", "旋转体体积"),
    (r"插值", "插值多项式"),
    (r"不动点", "不动点迭代"),
]


def _curated_haystack(node: Node) -> str:
    text = " ".join(part for part in (node.title, node.statement, node.label) if part)
    # OCR/LaTeX may double-escape backslashes; normalize for keyword matching.
    return re.sub(r"\\+", r"\\", text)


def strong_name(node: Node) -> str:
    text = _curated_haystack(node)
    for pattern, name in _STRONG:
        if re.search(pattern, text, re.IGNORECASE):
            return name
    return ""


def curated_name(node: Node) -> str:
    text = _curated_haystack(node)
    for pattern, name in _CURATED:
        if re.search(pattern, text, re.IGNORECASE):
            return name
    return ""


def clean_title(node: Node) -> str:
    title = node.title.strip().strip("。；;：:，,.")
    if not title or title in GENERIC_LABELS:
        return ""
    if title == node.label or re.fullmatch(r"\d+", title):
        return ""
    if len(title) > 32 or "$" in title or "\\" in title:
        return ""
    if "则" in title or re.match(r"^(设|若|令|对|存在|任意|一切|函数|数列)", title):
        return ""
    return title


def section_topic(node: Node) -> str:
    section = re.sub(r"^§\s*\d+\s*", "", node.section).strip(" ：:·")
    if 3 <= len(section) <= 28 and "$" not in section:
        return section
    return ""


def derived_name(node: Node) -> str:
    text = MATH_RE.sub(" ", node.statement)
    text = re.sub(
        r"^\s*(定义|定理|引理|推论|命题)\s*[0-9.′'’*＊]*\s*[（(][^）)]{1,40}[）)]\s*",
        "",
        text,
    )
    text = re.sub(
        r"^\s*(定义|定理|引理|推论|命题)\s*[0-9.′'’*＊]*\s*", "", text
    )
    text = re.split(r"[。；;]", text, maxsplit=1)[0]
    text = re.sub(r"\s+", "", text).strip("，,。；;：: ")
    text = re.sub(r"^(设|若|令|如果|对于|存在|任意|一切)+", "", text)
    if len(text) > 28:
        text = text[:28] + "…"
    if len(text) >= 4:
        return text
    return node.label


def _base_name(node: Node) -> str:
    return (
        strong_name(node)
        or clean_title(node)
        or curated_name(node)
        or section_topic(node)
        or derived_name(node)
        or node.label
    )


def _suffix_label(node: Node) -> str:
    label = node.label.replace(" ", "")
    if any(character.isdigit() for character in label):
        return label
    suffix = str(node.id).split(":")[-1]
    return suffix or node.label


def apply_display_names(
    nodes: list[Node], overrides: dict[str, Any] | None = None
) -> None:
    overrides = overrides or {}
    theorem_nodes = [node for node in nodes if node.kind == "theorem"]

    for node in theorem_nodes:
        override = str(overrides.get(node.id, "")).strip()
        node.display_name = override or _base_name(node)

    counts = Counter((node.book_id, node.display_name) for node in theorem_nodes)
    for node in theorem_nodes:
        if counts[(node.book_id, node.display_name)] <= 1:
            continue
        if node.id in overrides:
            continue
        node.display_name = f"{node.display_name}（{_suffix_label(node)}）"

    # Same label can be repeated by a theorem and a corollary (e.g. both
    # numbered 10.1.1). Use the node id suffix as a final tie-breaker.
    counts = Counter((node.book_id, node.display_name) for node in theorem_nodes)
    for node in theorem_nodes:
        if counts[(node.book_id, node.display_name)] <= 1 or node.id in overrides:
            continue
        suffix = str(node.id).split(":")[-1]
        node.display_name = f"{node.display_name}·{suffix}"
