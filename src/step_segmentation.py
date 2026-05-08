from __future__ import annotations

from dataclasses import dataclass

from mathml_parser import collect_structural_labels, parse_math_root
from models import ASTNode, StepRecord
from q34_rules import infer_step_labels
from xml_loader import MathEntry


RELATION_KINDS = {
    "eq",
    "neq",
    "lt",
    "gt",
    "leq",
    "geq",
    "implies",
    "iff",
    "definition",
}


@dataclass
class SegmentedStep:
    source_equation_id: str
    source_math_id: str | None
    ast: ASTNode
    description: str
    raw_text: str | None = None
    cue_text: str | None = None


def is_word_like(node: ASTNode) -> bool:
    if node.kind == "identifier":
        return True
    if node.kind == "times" and node.children:
        return all(is_word_like(child) for child in node.children)
    return False


def flatten_word_like(node: ASTNode) -> str:
    if node.kind == "identifier":
        return node.value or ""
    return "".join(flatten_word_like(child) for child in node.children or [])


def summarize_cue_nodes(nodes: list[ASTNode]) -> str | None:
    parts: list[str] = []
    for node in nodes:
        if is_word_like(node):
            text = flatten_word_like(node)
            if text:
                parts.append(text)
            continue
        if (
            node.kind == "eq"
            and node.children
            and len(node.children) == 2
            and is_word_like(node.children[0])
        ):
            lhs_text = flatten_word_like(node.children[0])
            if lhs_text:
                parts.append(lhs_text)
    if not parts:
        return None
    return " | ".join(parts)


def choose_primary_expression(nodes: list[ASTNode]) -> tuple[ASTNode, str | None]:
    if not nodes:
        raise ValueError("Cannot segment an empty node list")

    if len(nodes) == 1:
        return nodes[0], None

    relation_indexes = [index for index, node in enumerate(nodes) if node.kind in RELATION_KINDS]
    if relation_indexes:
        primary_index = relation_indexes[-1]
        cue_nodes = nodes[:primary_index]
        return nodes[primary_index], summarize_cue_nodes(cue_nodes)

    return nodes[-1], summarize_cue_nodes(nodes[:-1])


def describe_step(equation_id: str | None, ast: ASTNode, row_index: int | None = None) -> str:
    parts = ["Discovered step"]
    if equation_id:
        parts.append(f"from {equation_id}")
    if row_index is not None:
        parts.append(f"row {row_index}")
    parts.append(f"({ast.kind})")
    return " ".join(parts)


def segment_math_entry(entry: MathEntry) -> list[SegmentedStep]:
    if entry.contentml is None:
        return []

    root_ast = parse_math_root(entry.contentml)
    source_equation_id = entry.equation_id or "UNKNOWN_EQUATION"

    if root_ast.kind == "matrix":
        segmented_steps: list[SegmentedStep] = []
        for row_index, row in enumerate(root_ast.children or [], start=1):
            if row.kind != "matrix_row" or not row.children:
                continue
            ast, cue_text = choose_primary_expression(row.children)
            segmented_steps.append(
                SegmentedStep(
                    source_equation_id=source_equation_id,
                    source_math_id=entry.math_id,
                    ast=ast,
                    description=describe_step(source_equation_id, ast, row_index=row_index),
                    raw_text=entry.text,
                    cue_text=cue_text,
                )
            )
        return segmented_steps

    if root_ast.kind == "formulae-sequence":
        segmented_steps = []
        for child_index, child in enumerate(root_ast.children or [], start=1):
            segmented_steps.append(
                SegmentedStep(
                    source_equation_id=source_equation_id,
                    source_math_id=entry.math_id,
                    ast=child,
                    description=f"Discovered step from {source_equation_id} sequence {child_index} ({child.kind})",
                    raw_text=entry.text,
                )
            )
        return segmented_steps

    return [
        SegmentedStep(
            source_equation_id=source_equation_id,
            source_math_id=entry.math_id,
            ast=root_ast,
            description=describe_step(source_equation_id, root_ast),
            raw_text=entry.text,
        )
    ]


def build_step_record(segmented_step: SegmentedStep, step_index: int) -> StepRecord:
    return StepRecord(
        step_id=f"Q34_FULL_STEP_{step_index}",
        source_equation_id=segmented_step.source_equation_id,
        source_math_id=segmented_step.source_math_id,
        description=segmented_step.description,
        ast=segmented_step.ast,
        structural_labels=collect_structural_labels(segmented_step.ast),
        step_labels=infer_step_labels(segmented_step.ast, cue_text=segmented_step.cue_text),
        raw_text=segmented_step.raw_text,
        cue_text=segmented_step.cue_text,
    )
