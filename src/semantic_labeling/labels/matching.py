from __future__ import annotations

from dataclasses import dataclass, field

from semantic_labeling.ast.parser import ExprNode



@dataclass
class PatternVar:
    name: str


@dataclass
class PatternNode:
    kind: str
    value: str | None = None
    children: list["PatternNode | PatternVar"] = field(default_factory=list)


Bindings = dict[str, ExprNode]


def var(name: str) -> PatternVar:
    return PatternVar(name)


def node(kind: str, *children, value: str | None = None) -> PatternNode:
    return PatternNode(kind=kind, value=value, children=list(children))


def number(value: str) -> PatternNode:
    return PatternNode(kind="number", value=value)


def flatten_multiply(expr: ExprNode) -> list[ExprNode]:
    if expr.kind != "multiply":
        return [expr]
    factors: list[ExprNode] = []
    for child in expr.children:
        factors.extend(flatten_multiply(child))
    return factors


def flatten_add(expr: ExprNode) -> list[ExprNode]:
    if expr.kind != "add":
        return [expr]
    terms: list[ExprNode] = []
    for child in expr.children:
        terms.extend(flatten_add(child))
    return terms


def same_shape(left: ExprNode, right: ExprNode) -> bool:
    if left.kind != right.kind:
        return False
    if len(left.children) != len(right.children):
        return False
    return all(same_shape(left_child, right_child) for left_child, right_child in zip(left.children, right.children))


def same_ast(left: ExprNode, right: ExprNode) -> bool:
    if left.kind != right.kind or left.value != right.value or len(left.children) != len(right.children):
        return False
    return all(same_ast(left_child, right_child) for left_child, right_child in zip(left.children, right.children))


def match_pattern(expr: ExprNode, pattern: PatternNode | PatternVar, bindings: Bindings | None = None) -> Bindings | None:
    if bindings is None:
        bindings = {}

    if isinstance(pattern, PatternVar):
        current = bindings.get(pattern.name)
        if current is None:
            bindings[pattern.name] = expr
            return bindings
        return bindings if same_ast(current, expr) else None

    if expr.kind != pattern.kind:
        return None
    if pattern.value is not None and expr.value != pattern.value:
        return None
    if len(expr.children) != len(pattern.children):
        return None

    current = dict(bindings)
    for expr_child, pattern_child in zip(expr.children, pattern.children):
        current = match_pattern(expr_child, pattern_child, current)
        if current is None:
            return None
    return current


def contains_subtree(expr: ExprNode, predicate) -> bool:
    if predicate(expr):
        return True
    return any(contains_subtree(child, predicate) for child in expr.children)
