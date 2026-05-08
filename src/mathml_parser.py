from __future__ import annotations

from lxml import etree

from models import ASTNode
from xml_loader import NS


MATHML_NS = NS["m"]


def local_name(tag: str) -> str:
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def normalize_symbol(text: str | None) -> str:
    if text is None:
        return ""
    return text.strip()


def first_semantic_child(math_element: etree._Element) -> etree._Element:
    semantics = math_element.find(f"{{{MATHML_NS}}}semantics")
    if semantics is None or len(semantics) == 0:
        raise ValueError("Expected m:semantics with a semantic child")
    return semantics[0]


def parse_operator(node: etree._Element) -> str:
    name = local_name(node.tag)
    if name == "csymbol":
        text = normalize_symbol(node.text)
        if text == "superscript":
            return "power"
        return text or "csymbol"
    return name


def parse_mathml(node: etree._Element) -> ASTNode:
    name = local_name(node.tag)

    if name == "ci":
        return ASTNode(kind="identifier", value=normalize_symbol(node.text))

    if name == "cn":
        return ASTNode(kind="number", value=normalize_symbol(node.text))

    if name == "cerror":
        return ASTNode(kind="error", children=[parse_mathml(child) for child in node])

    if name == "matrix":
        return ASTNode(kind="matrix", children=[parse_mathml(child) for child in node])

    if name == "matrixrow":
        return ASTNode(kind="matrix_row", children=[parse_mathml(child) for child in node])

    if name == "apply":
        children = list(node)
        operator = parse_operator(children[0])
        return ASTNode(
            kind=operator,
            children=[parse_mathml(child) for child in children[1:]],
        )

    if len(node) == 0:
        return ASTNode(kind=name)

    return ASTNode(kind=name, children=[parse_mathml(child) for child in node])


def parse_math_root(math_element: etree._Element) -> ASTNode:
    return parse_mathml(first_semantic_child(math_element))


def collect_structural_labels(node: ASTNode) -> list[str]:
    labels: set[str] = set()

    def visit(current: ASTNode) -> None:
        labels.add(current.kind.upper())
        for child in current.children or []:
            visit(child)

    visit(node)
    return sorted(labels)
