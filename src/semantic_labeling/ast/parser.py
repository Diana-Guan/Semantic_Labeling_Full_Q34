from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from lxml import etree

from semantic_labeling.io.xml_loader import MathUnit, NS, SourceRef


# This file does two jobs that belong closely together:
# it turns MathML into AST nodes, and it breaks larger displays into steps.
# I combined them on purpose so the AST logic and the step-building logic stay
# in one place and are easier to reason about while we rebuild the project.

MATHML_NS = NS["m"]
OPERATOR_ALIASES = {
    "times": "multiply",
    "minus": "subtract",
    "plus": "add",
    "formulae-sequence": "sequence",
}
FUNCTION_ALIASES = {
    "sine": "sin",
    "cosine": "cos",
    "tangent": "tan",
    "secant": "sec",
}
RELATION_KINDS = {"eq", "neq", "lt", "gt", "leq", "geq", "implies", "iff", "definition"}


@dataclass
class ExprNode:
    node_id: str
    kind: str
    value: str | None = None
    children: list["ExprNode"] = field(default_factory=list)
    source_ref: SourceRef | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "node_id": self.node_id,
            "kind": self.kind,
            "children": [child.to_dict() for child in self.children],
        }
        if self.value is not None:
            payload["value"] = self.value
        return payload


@dataclass
class Step:
    step_id: str
    equation_id: str
    math_id: str | None
    order_index: int
    original_expression: str | None
    ast: ExprNode
    cue_text: str | None = None
    labels: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "step_id": self.step_id,
            "equation_id": self.equation_id,
            "order_index": self.order_index,
            "original_expression": self.original_expression,
            "labels": self.labels,
        }
        if self.math_id is not None:
            payload["math_id"] = self.math_id
        return payload


def local_name(tag: str) -> str:
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def normalize_symbol(text: str | None) -> str:
    if text is None:
        return ""
    return text.strip()


def build_node_id(node: etree._Element, fallback: str) -> str:
    return node.get("{http://www.w3.org/XML/1998/namespace}id") or fallback


def first_semantic_child(math_element: etree._Element) -> etree._Element:
    semantics = math_element.find(f"{{{MATHML_NS}}}semantics")
    if semantics is None or len(semantics) == 0:
        raise ValueError("Expected m:semantics with a semantic child")
    return semantics[0]


def parse_operator(node: etree._Element) -> tuple[str, dict[str, object]]:
    name = local_name(node.tag)
    if name == "csymbol":
        text = normalize_symbol(node.text)
        if text == "superscript":
            return "power", {}
        if text == "missing-subexpression":
            return "unknown", {"raw_operator": text}
        normalized = FUNCTION_ALIASES.get(text, text or "unknown")
        return OPERATOR_ALIASES.get(normalized, normalized), {"raw_operator": text}
    return OPERATOR_ALIASES.get(FUNCTION_ALIASES.get(name, name), name), {}


def parse_mathml(node: etree._Element, source_ref: SourceRef, path: str = "root") -> ExprNode:
    name = local_name(node.tag)
    node_id = build_node_id(node, path)

    if name == "ci":
        return ExprNode(node_id=node_id, kind="identifier", value=normalize_symbol(node.text), source_ref=source_ref)

    if name == "cn":
        return ExprNode(node_id=node_id, kind="number", value=normalize_symbol(node.text), source_ref=source_ref)

    if name == "cerror":
        return ExprNode(
            node_id=node_id,
            kind="error",
            children=[parse_mathml(child, source_ref, f"{path}.{index}") for index, child in enumerate(node)],
            source_ref=source_ref,
        )

    if name == "matrix":
        return ExprNode(
            node_id=node_id,
            kind="matrix",
            children=[parse_mathml(child, source_ref, f"{path}.{index}") for index, child in enumerate(node)],
            source_ref=source_ref,
        )

    if name == "matrixrow":
        return ExprNode(
            node_id=node_id,
            kind="matrix_row",
            children=[parse_mathml(child, source_ref, f"{path}.{index}") for index, child in enumerate(node)],
            source_ref=source_ref,
        )

    if name == "apply":
        children = list(node)
        operator, annotations = parse_operator(children[0])
        parsed_children = [
            parse_mathml(child, source_ref, f"{path}.{index + 1}")
            for index, child in enumerate(children[1:])
        ]
        return ExprNode(
            node_id=node_id,
            kind=operator,
            children=parsed_children,
            source_ref=source_ref,
        )

    if name == "csymbol":
        return ExprNode(
            node_id=node_id,
            kind="unknown",
            value=normalize_symbol(node.text) or None,
            source_ref=source_ref,
        )

    return ExprNode(
        node_id=node_id,
        kind=OPERATOR_ALIASES.get(FUNCTION_ALIASES.get(name, name), name),
        children=[parse_mathml(child, source_ref, f"{path}.{index}") for index, child in enumerate(node)],
        source_ref=source_ref,
    )


def parse_math_root(math_element: etree._Element, source_ref: SourceRef) -> ExprNode:
    return parse_mathml(first_semantic_child(math_element), source_ref=source_ref)


def is_word_like(node: ExprNode) -> bool:
    if node.kind == "identifier":
        return True
    if node.kind == "multiply":
        return all(is_word_like(child) for child in node.children)
    return False


def flatten_word_like(node: ExprNode) -> str:
    if node.kind == "identifier":
        return node.value or ""
    return "".join(flatten_word_like(child) for child in node.children)


def summarize_cue(nodes: list[ExprNode]) -> str | None:
    parts: list[str] = []
    for node in nodes:
        if is_word_like(node):
            text = flatten_word_like(node)
            if text:
                parts.append(text)
    if not parts:
        return None
    return " ".join(parts)


def normalize_cue_text(cue_text: str | None) -> str:
    if not cue_text:
        return ""
    return unicodedata.normalize("NFKD", cue_text).encode("ascii", "ignore").decode("ascii").lower()


def choose_expression(nodes: list[ExprNode]) -> tuple[ExprNode, str | None]:
    if len(nodes) == 1:
        return nodes[0], None

    # Some aligned rows separate lhs, relation symbol, and rhs into different cells.
    # When that happens, I stitch them back into one relation node so later label
    # detection sees a normal equation instead of a lonely "=" token.
    for index, node in enumerate(nodes):
        if node.kind in RELATION_KINDS and not node.children and 0 < index < len(nodes) - 1:
            left = nodes[index - 1]
            right = nodes[index + 1]
            return (
                ExprNode(
                    node_id=node.node_id,
                    kind=node.kind,
                    children=[left, right],
                    source_ref=node.source_ref,
                ),
                summarize_cue(nodes[: max(index - 1, 0)]),
            )

    relation_indexes = [index for index, node in enumerate(nodes) if node.kind in RELATION_KINDS]
    if relation_indexes:
        relation_index = relation_indexes[-1]
        return nodes[relation_index], summarize_cue(nodes[:relation_index])

    return nodes[-1], summarize_cue(nodes[:-1])


def build_steps(units: list[MathUnit]) -> list[Step]:
    steps: list[Step] = []
    step_index = 1

    for unit in units:
        if unit.contentml is None:
            continue

        root = parse_math_root(unit.contentml, unit.source_ref)
        segmented: list[tuple[ExprNode, str | None]]
        if root.kind == "matrix":
            segmented = []
            for row in root.children:
                if row.kind != "matrix_row" or not row.children:
                    continue
                segmented.append(choose_expression(row.children))
        elif root.kind == "sequence":
            segmented = [(child, None) for child in root.children]
        else:
            segmented = [(root, None)]

        equation_id = unit.source_ref.equation_id or "UNKNOWN_EQUATION"
        for ast, cue_text in segmented:
            steps.append(
                Step(
                    step_id=f"STEP_{step_index}",
                    equation_id=equation_id,
                    math_id=unit.source_ref.math_id,
                    order_index=step_index - 1,
                    original_expression=unit.text,
                    ast=ast,
                    cue_text=normalize_cue_text(cue_text),
                )
            )
            step_index += 1

    return steps
