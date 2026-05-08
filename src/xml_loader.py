"""Use lxml to load LaTeXML combined XMath + ContentML xml files into Python.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from lxml import etree


NS = {
    "ltx": "http://dlmf.nist.gov/LaTeXML",
    "m": "http://www.w3.org/1998/Math/MathML",
    "xml": "http://www.w3.org/XML/1998/namespace",
}

XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


@dataclass
class MathEntry:
    source_file: Path
    equation_id: str | None
    math_id: str | None
    tex: str | None
    text: str | None
    contentml: etree._Element | None
    xmath: etree._Element | None

    def to_debug_dict(self) -> dict[str, object]:
        return {
            "source_file": str(self.source_file),
            "equation_id": self.equation_id,
            "math_id": self.math_id,
            "tex": self.tex,
            "text": self.text,
            "contentml_present": self.contentml is not None,
            "xmath_present": self.xmath is not None,
            "contentml_xml": element_to_string(self.contentml),
            "xmath_xml": element_to_string(self.xmath),
        }


def element_to_string(element: etree._Element | None) -> str | None:
    if element is None:
        return None
    return etree.tostring(element, pretty_print=True, encoding="unicode")


def load_tree(xml_path: str | Path) -> etree._ElementTree:
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(str(xml_path), parser)


def extract_math_entry(
    equation: etree._Element,
    source_file: str | Path,
) -> MathEntry | None:
    math_node = equation.find(".//ltx:Math", namespaces=NS)
    if math_node is None:
        return None

    contentml = math_node.find("m:math", namespaces=NS)
    annotation = math_node.find('.//m:annotation-xml[@encoding="application/x-latexml"]', namespaces=NS)
    xmath = annotation.find("ltx:XMath", namespaces=NS) if annotation is not None else None

    return MathEntry(
        source_file=Path(source_file),
        equation_id=equation.get(XML_ID),
        math_id=math_node.get(XML_ID),
        tex=math_node.get("tex"),
        text=math_node.get("text"),
        contentml=contentml,
        xmath=xmath,
    )


def load_combined_file(xml_path: str | Path) -> list[MathEntry]:
    tree = load_tree(xml_path)
    root = tree.getroot()

    entries: list[MathEntry] = []
    for equation in root.findall(".//ltx:equation", namespaces=NS):
        entry = extract_math_entry(equation, xml_path)
        if entry is not None:
            entries.append(entry)
    return entries


def iter_combined_files(directory: str | Path) -> Iterator[Path]:
    base = Path(directory)
    for path in sorted(base.glob("*.xml")):
        yield path


def load_combined_directory(directory: str | Path) -> list[MathEntry]:
    entries: list[MathEntry] = []
    for path in iter_combined_files(directory):
        entries.extend(load_combined_file(path))
    return entries


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load LaTeXML combined XMath+ContentML XML files.",
    )
    parser.add_argument(
        "path",
        help="XML file or directory of XML files to load.",
    )
    parser.add_argument(
        "--json-out",
        help="Optional path to write debug JSON.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="How many entries to print to stdout.",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    input_path = Path(args.path)
    if input_path.is_dir():
        entries = load_combined_directory(input_path)
    else:
        entries = load_combined_file(input_path)

    print(f"Loaded {len(entries)} math entries from {input_path}")
    for entry in entries[: args.limit]:
        print()
        print(f"equation_id: {entry.equation_id}")
        print(f"math_id: {entry.math_id}")
        print(f"tex: {entry.tex}")
        print(f"text: {entry.text}")
        print(f"contentml_present: {entry.contentml is not None}")
        print(f"xmath_present: {entry.xmath is not None}")

    if args.json_out:
        debug_payload = [entry.to_debug_dict() for entry in entries]
        output_path = Path(args.json_out)
        output_path.write_text(
            json.dumps(debug_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nWrote debug JSON to {output_path}")


if __name__ == "__main__":
    main()
