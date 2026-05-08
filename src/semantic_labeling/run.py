from __future__ import annotations

import argparse
import json
from pathlib import Path

from semantic_labeling.ast.parser import ExprNode, build_steps
from semantic_labeling.io.xml_loader import load_combined_file
from semantic_labeling.labels.definitions import LABEL_DEFINITIONS
from semantic_labeling.labels.q34_labels import detect_solution_labels, detect_step_labels


# This is the single entry point for the rebuilt project.
# It keeps the flow very plain: load XML, build AST steps, detect labels,
# format a readable AST tree, and write JSON. Nothing extra is hidden behind
# framework layers.


def ast_tree_lines(node: ExprNode, indent: int = 0) -> list[str]:
    prefix = "  " * indent
    if node.value is not None:
        lines = [f"{prefix}{node.kind}({node.value})"]
    else:
        lines = [f"{prefix}{node.kind}"]
    for child in node.children:
        lines.extend(ast_tree_lines(child, indent + 1))
    return lines


def run_q34(input_path: str | Path) -> dict[str, object]:
    units = load_combined_file(input_path)
    steps = build_steps(units)

    for step in steps:
        step.labels = detect_step_labels(step)

    return {
        "metadata": {
            "pipeline_name": "semantic_labeling_q34",
            "focus": ["ast", "labels"],
        },
        "label_definitions": list(LABEL_DEFINITIONS.values()),
        "labels": detect_solution_labels(steps),
        "equations": [
            {
                "equation_id": step.equation_id,
                "step_id": step.step_id,
                "original_expression": step.original_expression,
                "labels": step.labels,
                "ast_tree": ast_tree_lines(step.ast),
            }
            for step in steps
        ],
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the rebuilt semantic labeling pipeline for Q34.")
    parser.add_argument(
        "--input",
        default=str(
            Path(__file__).resolve().parents[2]
            / "data"
            / "input"
            / "Q34_Version3_mathonly.xml"
        ),
        help="Combined XML file to process.",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parents[2] / "data" / "output" / "q34_semantic_labels.json"),
        help="JSON file to write.",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    payload = run_q34(Path(args.input))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(payload['equations'])} equations to {output_path}")


if __name__ == "__main__":
    main()
