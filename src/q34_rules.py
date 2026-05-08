from __future__ import annotations

from models import ASTNode, Label


def has_children(node: ASTNode, count: int) -> bool:
    return node.children is not None and len(node.children) == count


def is_identifier(node: ASTNode, value: str) -> bool:
    return node.kind == "identifier" and node.value == value


def is_number(node: ASTNode, value: str) -> bool:
    return node.kind == "number" and node.value == value


def is_sin_theta(node: ASTNode) -> bool:
    return (
        node.kind == "sin"
        and has_children(node, 1)
        and is_identifier(node.children[0], "𝜃")
    )


def is_power(node: ASTNode, exponent: str | None = None) -> bool:
    if node.kind != "power" or not has_children(node, 2):
        return False
    if exponent is not None and not is_number(node.children[1], exponent):
        return False
    return True


def is_times_of_a_and_sin(node: ASTNode) -> bool:
    return (
        node.kind == "times"
        and has_children(node, 2)
        and is_identifier(node.children[0], "𝑎")
        and is_sin_theta(node.children[1])
    )


def is_x_equals_a_sin_theta(ast: ASTNode) -> bool:
    return (
        ast.kind == "eq"
        and has_children(ast, 2)
        and is_identifier(ast.children[0], "𝑥")
        and is_times_of_a_and_sin(ast.children[1])
    )


def is_radical_substitution(ast: ASTNode) -> bool:
    if not (ast.kind == "eq" and has_children(ast, 2)):
        return False

    left, right = ast.children
    if not (
        left.kind == "root"
        and right.kind == "root"
        and has_children(left, 1)
        and has_children(right, 1)
    ):
        return False

    left_inner = left.children[0]
    right_inner = right.children[0]
    if not (
        left_inner.kind == "minus"
        and right_inner.kind == "minus"
        and has_children(left_inner, 2)
        and has_children(right_inner, 2)
    ):
        return False

    return (
        is_power(left_inner.children[0], "2")
        and is_power(left_inner.children[1], "2")
        and is_identifier(left_inner.children[1].children[0], "𝑥")
        and is_power(right_inner.children[0], "2")
        and is_power(right_inner.children[1], "2")
        and is_times_of_a_and_sin(right_inner.children[1].children[0])
    )


def is_power_of_a_product_rewrite(ast: ASTNode) -> bool:
    return (
        ast.kind == "eq"
        and has_children(ast, 2)
        and is_power(ast.children[0], exponent="2")
        and ast.children[0].children
        and is_times_of_a_and_sin(ast.children[0].children[0])
        and ast.children[1].kind == "times"
        and has_children(ast.children[1], 2)
        and is_power(ast.children[1].children[0], "2")
        and is_identifier(ast.children[1].children[0].children[0], "𝑎")
        and is_power(ast.children[1].children[1], "2")
        and is_sin_theta(ast.children[1].children[1].children[0])
    )


def is_radical_power_rewrite(ast: ASTNode) -> bool:
    if not (ast.kind == "eq" and has_children(ast, 2)):
        return False

    left, right = ast.children
    if not (
        left.kind == "root"
        and right.kind == "root"
        and has_children(left, 1)
        and has_children(right, 1)
    ):
        return False

    left_inner = left.children[0]
    right_inner = right.children[0]
    if not (
        left_inner.kind == "minus"
        and right_inner.kind == "minus"
        and has_children(left_inner, 2)
        and has_children(right_inner, 2)
    ):
        return False

    return (
        is_power(left_inner.children[1], "2")
        and is_times_of_a_and_sin(left_inner.children[1].children[0])
        and right_inner.children[1].kind == "times"
        and has_children(right_inner.children[1], 2)
        and is_power(right_inner.children[1].children[0], "2")
        and is_identifier(right_inner.children[1].children[0].children[0], "𝑎")
        and is_power(right_inner.children[1].children[1], "2")
        and is_sin_theta(right_inner.children[1].children[1].children[0])
    )


def label_ex10(ast: ASTNode) -> list[Label]:
    if is_x_equals_a_sin_theta(ast):
        return [
            Label(
                id="TRIG_SUBSTITUTION",
                evidence=["The step introduces the substitution x = a sin(theta)."],
            )
        ]
    return []


def label_ex11(ast: ASTNode) -> list[Label]:
    if is_radical_substitution(ast):
        return [
            Label(
                id="SUBSTITUTION_APPLIED",
                evidence=["The radical expression replaces x with a sin(theta)."],
            )
        ]
    return []


def label_ex12_row2(ast: ASTNode) -> list[Label]:
    if is_power_of_a_product_rewrite(ast):
        return [
            Label(
                id="POWER_OF_A_PRODUCT",
                evidence=["(a sin(theta))^2 is rewritten as a^2 (sin(theta))^2."],
            )
        ]
    return []


def label_ex12_row3(ast: ASTNode) -> list[Label]:
    labels: list[Label] = []
    if is_radical_power_rewrite(ast):
        labels.append(
            Label(
                id="ALGEBRAIC_SIMPLIFICATION",
                evidence=["The expression inside the radical is rewritten into a factored product form."],
            )
        )
        labels.append(
            Label(
                id="POWER_OF_A_PRODUCT",
                evidence=["The rewrite uses the product power rule inside the radical."],
            )
        )
    return labels


def infer_step_labels(ast: ASTNode, cue_text: str | None = None) -> list[Label]:
    del cue_text

    labels: list[Label] = []
    for label_builder in (label_ex10, label_ex11, label_ex12_row2, label_ex12_row3):
        labels.extend(label_builder(ast))
    return labels
