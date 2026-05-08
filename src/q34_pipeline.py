from __future__ import annotations

from pathlib import Path

from lxml import etree

from mathml_parser import collect_structural_labels, parse_math_root
from models import ASTNode, StepRecord
from q34_rules import label_ex10, label_ex11, label_ex12_row2, label_ex12_row3
from step_segmentation import build_step_record, segment_math_entry
from xml_loader import NS, load_combined_file, load_tree


def find_math_by_id(root: etree._Element, math_id: str) -> etree._Element:
    math_nodes = root.xpath(f'.//ltx:Math[@xml:id="{math_id}"]', namespaces=NS)
    if not math_nodes:
        raise ValueError(f"Could not find Math node {math_id}")
    math_node = math_nodes[0]
    contentml = math_node.find("m:math", namespaces=NS)
    if contentml is None:
        raise ValueError(f"{math_id} has no ContentML subtree")
    return contentml


def extract_matrix_row_equations(ast: ASTNode) -> tuple[ASTNode, ASTNode]:
    if ast.kind != "matrix" or not ast.children or len(ast.children) < 3:
        raise ValueError("Expected a matrix with at least three rows")

    row2 = ast.children[1]
    row3 = ast.children[2]
    if row2.kind != "matrix_row" or row3.kind != "matrix_row":
        raise ValueError("Expected matrix_row nodes in the aligned derivation")
    if not row2.children or not row3.children:
        raise ValueError("Expected populated aligned derivation rows")

    return row2.children[-1], row3.children[-1]


def build_q34_mvp_steps(root: etree._Element) -> list[StepRecord]:
    ex10_ast = parse_math_root(find_math_by_id(root, "S0.Ex10.m1"))
    ex11_ast = parse_math_root(find_math_by_id(root, "S0.Ex11X.m3"))
    ex12_root_ast = parse_math_root(find_math_by_id(root, "S0.Ex12.m1"))
    ex12_row2_ast, ex12_row3_ast = extract_matrix_row_equations(ex12_root_ast)

    return [
        StepRecord(
            step_id="Q34_STEP_1",
            source_equation_id="S0.Ex10",
            description="Introduce the trig substitution x = a sin(theta).",
            ast=ex10_ast,
            structural_labels=collect_structural_labels(ex10_ast),
            step_labels=label_ex10(ex10_ast),
        ),
        StepRecord(
            step_id="Q34_STEP_2",
            source_equation_id="S0.Ex11X",
            description="Apply the substitution to the radical sqrt(a^2 - x^2).",
            ast=ex11_ast,
            structural_labels=collect_structural_labels(ex11_ast),
            step_labels=label_ex11(ex11_ast),
        ),
        StepRecord(
            step_id="Q34_STEP_3",
            source_equation_id="S0.Ex12",
            description="Rewrite (a sin(theta))^2 using the power-of-a-product rule.",
            ast=ex12_row2_ast,
            structural_labels=collect_structural_labels(ex12_row2_ast),
            step_labels=label_ex12_row2(ex12_row2_ast),
        ),
        StepRecord(
            step_id="Q34_STEP_4",
            source_equation_id="S0.Ex12",
            description="Simplify the substituted radical using the same rewrite inside the root.",
            ast=ex12_row3_ast,
            structural_labels=collect_structural_labels(ex12_row3_ast),
            step_labels=label_ex12_row3(ex12_row3_ast),
        ),
    ]


def build_output_payload(steps: list[StepRecord], input_path: Path) -> dict[str, object]:
    return {
        "source_file": str(input_path),
        "scope": {
            "equations": ["S0.Ex10", "S0.Ex11X", "S0.Ex12"],
            "notes": "Minimal Q34 MVP focused on trig substitution and follow-up rewrites.",
        },
        "steps": [step.to_dict() for step in steps],
    }


def run_q34_mvp(input_path: Path) -> dict[str, object]:
    tree = load_tree(input_path)
    root = tree.getroot()
    steps = build_q34_mvp_steps(root)
    return build_output_payload(steps, input_path)


def run_q34_full(input_path: Path) -> dict[str, object]:
    entries = load_combined_file(input_path)
    segmented_steps = []
    for entry in entries:
        segmented_steps.extend(segment_math_entry(entry))

    steps = [
        build_step_record(segmented_step, step_index)
        for step_index, segmented_step in enumerate(segmented_steps, start=1)
    ]

    return {
        "source_file": str(input_path),
        "scope": {
            "equations": sorted({step.source_equation_id for step in steps}),
            "notes": "Full Q34 step discovery with matrix-row and sequence segmentation.",
        },
        "steps": [step.to_dict() for step in steps],
    }
