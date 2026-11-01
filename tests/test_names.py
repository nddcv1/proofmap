from proofmap.model import Node
from proofmap.names import apply_display_names


def theorem(title, statement="", section="§ 1 数列极限", label="定理 1.1"):
    return Node(
        id="b:定理1.1",
        kind="theorem",
        subkind="theorem",
        label=label,
        title=title,
        aliases=[label],
        book_id="b",
        chapter="第1章",
        section=section,
        pdf_page=1,
        printed_page=1,
        statement=statement,
        source_chunks=[],
    )


def name_of(node):
    apply_display_names([node])
    return node.display_name


def test_curated_named_theorem_wins():
    assert name_of(theorem("Rolle 定理", "若 f(a)=f(b)，则存在 ξ。")) == "Rolle 定理"


def test_short_clean_title_is_used():
    assert name_of(theorem("三角不等式", "设 x, y 为实数。")) == "三角不等式"


def test_math_heavy_title_falls_back_to_curated_keyword():
    node = theorem(
        "设 $x_n$ 收敛，则它的任何子列收敛于同一极限",
        "若 $x_n\\to a$，则任意子列 $x_{n_k}\\to a$。",
    )
    name = name_of(node)
    assert name == "子列收敛性"
    assert "$" not in name


def test_auto_name_is_short_and_math_free():
    node = theorem(
        "设 $x_n$ 是无穷大量",
        "设 $x_n\\neq0$，则 $|x_n|\\to+\\infty$。",
    )
    name = name_of(node)
    assert name
    assert "$" not in name
    assert len(name) <= 32


def test_double_escaped_latex_still_matches():
    node = theorem(
        "若 $\\\\lim_{x\\\\to x_0}f(x)=A\\\\neq0$，则存在邻域",
        "若 $\\\\lim f=A\\\\neq0$，则存在 $\\\\delta>0$。",
    )
    assert name_of(node) == "函数极限的局部保号性"


def test_override_wins():
    node = theorem("Rolle 定理", "若 f(a)=f(b)。")
    apply_display_names([node], {"b:定理1.1": "罗尔中值定理"})
    assert node.display_name == "罗尔中值定理"
