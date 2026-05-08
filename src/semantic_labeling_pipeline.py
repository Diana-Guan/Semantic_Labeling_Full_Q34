from __future__ import annotations

import argparse
import json
from pathlib import Path

from q34_pipeline import run_q34_full, run_q34_mvp


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run semantic labeling pipelines for local LaTeXML inputs.",
    )
    parser.add_argument(
        "--pipeline",
        default="q34_mvp",
        choices=["q34_mvp", "q34_full"],
        help="Pipeline implementation to run.",
    )
    parser.add_argument(
        "--input",
        default=str(Path(__file__).resolve().parent.parent / "data" / "input" / "Q34_Version3_mathonly.xml"),
        help="Combined XML file to process.",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parent.parent / "data" / "output" / "q34_mvp_labels.json"),
        help="JSON file to write.",
    )
    return parser


def run_pipeline(pipeline_name: str, input_path: Path) -> dict[str, object]:
    if pipeline_name == "q34_mvp":
        return run_q34_mvp(input_path)
    if pipeline_name == "q34_full":
        return run_q34_full(input_path)
    raise ValueError(f"Unsupported pipeline: {pipeline_name}")


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    payload = run_pipeline(args.pipeline, input_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Wrote {len(payload['steps'])} steps to {output_path}")


if __name__ == "__main__":
    main()
