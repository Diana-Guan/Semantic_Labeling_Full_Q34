from __future__ import annotations

from semantic_labeling.ast.parser import ExprNode, Step
from semantic_labeling.labels.definitions import make_label
from semantic_labeling.labels.matching import contains_subtree, flatten_multiply, match_pattern, node, number, var


# This file is Q34 specific.
# The point is not to build a universal calculus labeler yet.
# The point is to capture the rules and techniques that really show up in Q34,

def is_eq(expr: ExprNode) -> bool:
    return expr.kind == "eq" and len(expr.children) == 2


def is_identifier(expr: ExprNode, value: str) -> bool:
    return expr.kind == "identifier" and expr.value == value


def contains_kind(expr: ExprNode, kind: str) -> bool:
    return contains_subtree(expr, lambda current: current.kind == kind)


def detect_fractional_exponent_to_root(step: Step) -> list[dict[str, str]]:
    expr = step.ast
    if not is_eq(expr):
        return []
    left, right = expr.children
    if left.kind == "power" and len(left.children) == 2 and left.children[1].kind == "divide" and contains_kind(right, "root"):
        return [make_label("FRACTIONAL_EXPONENT_TO_ROOT")]
    return []


def detect_power_of_a_product(step: Step) -> list[dict[str, str]]:
    pattern = node(
        "eq",
        node("power", node("multiply", var("A"), var("B")), var("N")),
        node("multiply", node("power", var("A"), var("N")), node("power", var("B"), var("N"))),
    )
    return [make_label("POWER_OF_A_PRODUCT")] if match_pattern(step.ast, pattern) is not None else []


def detect_radical_rewrite(step: Step) -> list[dict[str, str]]:
    expr = step.ast
    if not is_eq(expr):
        return []
    left, right = expr.children
    if contains_kind(left, "root") and contains_kind(right, "root") and match_pattern(left, right) is None:
        return [make_label("RADICAL_REWRITE")]
    return []


def detect_constant_substitution(step: Step) -> list[dict[str, str]]:
    expr = step.ast
    if not is_eq(expr):
        return []
    left, right = expr.children
    if (left.kind == "identifier" and contains_kind(right, "number")) or (left.kind == "power" and contains_kind(right, "number")):
        return [make_label("CONSTANT_SUBSTITUTION")]
    return []


def detect_factoring(step: Step) -> list[dict[str, str]]:
    if not is_eq(step.ast):
        return []
    left, right = step.ast.children
    if len(flatten_multiply(right)) > 1 and contains_kind(right, "subtract") and not contains_kind(left, "subtract"):
        return [make_label("FACTORING")]
    return []


def detect_trig_identity(step: Step) -> list[dict[str, str]]:
    sin_cos_pattern = node(
        "eq",
        node("subtract", number("1"), node("power", node("sin", var("T")), number("2"))),
        node("power", node("cos", var("T")), number("2")),
    )
    tan_sec_pattern = node(
        "eq",
        node("power", node("tan", var("T")), number("2")),
        node("subtract", node("power", node("sec", var("T")), number("2")), number("1")),
    )
    if match_pattern(step.ast, sin_cos_pattern) is not None or match_pattern(step.ast, tan_sec_pattern) is not None:
        return [make_label("TRIG_IDENTITY")]
    return []


def detect_root_product_rule(step: Step) -> list[dict[str, str]]:
    pattern = node(
        "eq",
        node("root", node("multiply", var("A"), var("B"))),
        node("multiply", node("root", var("A")), node("root", var("B"))),
    )
    return [make_label("ROOT_PRODUCT_RULE")] if match_pattern(step.ast, pattern) is not None else []


def detect_sqrt_to_abs(step: Step) -> list[dict[str, str]]:
    pattern = node(
        "eq",
        node("root", node("power", var("U"), number("2"))),
        node("abs", var("U")),
    )
    return [make_label("SQRT_TO_ABS")] if match_pattern(step.ast, pattern) is not None else []


def detect_trig_square_rewrite(step: Step) -> list[dict[str, str]]:
    if not is_eq(step.ast):
        return []
    left, right = step.ast.children
    left_has_plain_trig = any(contains_kind(left, kind) for kind in ("sin", "cos", "tan"))
    right_has_trig_power = any(
        contains_subtree(
            right,
            lambda current, trig=kind: current.kind == "power"
            and len(current.children) == 2
            and current.children[0].kind == trig
            and current.children[1].kind == "number"
        )
        for kind in ("sin", "cos", "tan")
    )
    if left_has_plain_trig and right_has_trig_power:
        return [make_label("TRIG_SQUARE_REWRITE")]
    return []


def detect_differentiation(step: Step) -> list[dict[str, str]]:
    if contains_kind(step.ast, "derivative"):
        return [make_label("DIFFERENTIATION")]
    return []


def detect_differential_rewrite(step: Step) -> list[dict[str, str]]:
    if is_eq(step.ast) and (
        contains_kind(step.ast.children[0], "differential") or contains_kind(step.ast.children[1], "differential")
    ):
        return [make_label("DIFFERENTIAL_REWRITE")]
    return []


def detect_integrand_substitution(step: Step) -> list[dict[str, str]]:
    if not is_eq(step.ast):
        return []
    left, right = step.ast.children
    if contains_kind(left, "integral") and contains_kind(right, "integral"):
        return [make_label("INTEGRAND_SUBSTITUTION")]
    return []


def detect_cancel_common_factor(step: Step) -> list[dict[str, str]]:
    if not is_eq(step.ast):
        return []
    left, right = step.ast.children
    if left.kind == "divide" and right.kind == "divide":
        left_num, left_den = left.children
        right_num, right_den = right.children
        if contains_subtree(left_num, lambda current: current.kind == "multiply") and same_denominator(left_den, right_den):
            return [make_label("CANCEL_COMMON_FACTOR")]
    return []


def detect_trig_ratio_rewrite(step: Step) -> list[dict[str, str]]:
    tan_pattern = node(
        "eq",
        node("tan", var("T")),
        node("divide", node("sin", var("T")), node("cos", var("T"))),
    )
    tan_sq_pattern = node(
        "eq",
        node("power", node("tan", var("T")), number("2")),
        node("divide", node("power", node("sin", var("T")), number("2")), node("power", node("cos", var("T")), number("2"))),
    )
    if match_pattern(step.ast, tan_pattern) is not None or match_pattern(step.ast, tan_sq_pattern) is not None:
        return [make_label("TRIG_RATIO_REWRITE")]
    return []


def detect_integral_split(step: Step) -> list[dict[str, str]]:
    expr = step.ast
    if not is_eq(expr):
        return []
    left, right = expr.children
    if contains_kind(left, "integral") and right.kind == "subtract" and all(child.kind == "integral" for child in right.children):
        return [make_label("INTEGRAL_SPLIT")]
    return []


def detect_antiderivative(step: Step) -> list[dict[str, str]]:
    if is_eq(step.ast) and contains_kind(step.ast, "integral") and any(
        contains_kind(step.ast, kind) for kind in ("tan", "sec", "identifier")
    ):
        return [make_label("ANTIDERIVATIVE")]
    return []


def detect_back_substitution(step: Step) -> list[dict[str, str]]:
    if not is_eq(step.ast):
        return []
    left, right = step.ast.children
    if is_identifier(left, "𝜃") and right.kind == "arcsin":
        return [make_label("BACK_SUBSTITUTION")]
    if contains_kind(step.ast, "arcsin"):
        return [make_label("BACK_SUBSTITUTION")]
    return []


def detect_reference_triangle(step: Step) -> list[dict[str, str]]:
    if contains_kind(step.ast, "tan") and contains_kind(step.ast, "root"):
        return [make_label("REFERENCE_TRIANGLE")]
    return []


STEP_DETECTORS = (
    detect_fractional_exponent_to_root,
    detect_power_of_a_product,
    detect_radical_rewrite,
    detect_constant_substitution,
    detect_factoring,
    detect_trig_identity,
    detect_root_product_rule,
    detect_sqrt_to_abs,
    detect_trig_square_rewrite,
    detect_differentiation,
    detect_differential_rewrite,
    detect_integrand_substitution,
    detect_cancel_common_factor,
    detect_trig_ratio_rewrite,
    detect_integral_split,
    detect_antiderivative,
    detect_back_substitution,
    detect_reference_triangle,
)


def detect_step_labels(step: Step) -> list[dict[str, str]]:
    labels: list[dict[str, str]] = []
    for detector in STEP_DETECTORS:
        labels.extend(detector(step))
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for label in labels:
        if label["label_id"] in seen:
            continue
        seen.add(label["label_id"])
        deduped.append(label)
    return deduped


def detect_solution_labels(steps: list[Step]) -> list[dict[str, str]]:
    # Right now I only promote one broad solution-level label.
    # The idea is to stay disciplined and only add more span logic when we have
    # strong reason to do so.
    all_steps = steps
    has_substitution = any(
        is_eq(step.ast)
        and len(step.ast.children) == 2
        and is_identifier(step.ast.children[0], "𝑥")
        and step.ast.children[1].kind in {"multiply", "sin", "tan", "sec"}
        for step in all_steps
    )
    has_radical = any(contains_kind(step.ast, "root") for step in all_steps)
    has_back_substitution = any(any(label["name"] == "BACK_SUBSTITUTION" for label in step.labels) for step in all_steps)
    has_trig_identity = any(any(label["name"] == "TRIG_IDENTITY" for label in step.labels) for step in all_steps)

    labels: list[dict[str, str]] = []
    if has_substitution and has_radical and (has_back_substitution or has_trig_identity):
        labels.append(make_label("TRIG_SUBSTITUTION"))
    return labels


def same_denominator(left: ExprNode, right: ExprNode) -> bool:
    if left.kind != right.kind or left.value != right.value or len(left.children) != len(right.children):
        return False
    return all(same_denominator(left_child, right_child) for left_child, right_child in zip(left.children, right.children))
