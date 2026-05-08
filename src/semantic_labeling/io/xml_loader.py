from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from lxml import etree


# This file deals with reading the XML and pulling out math blocks in order.

NS = {
    "ltx": "http://dlmf.nist.gov/LaTeXML",
    "m": "http://www.w3.org/1998/Math/MathML",
    "xml": "http://www.w3.org/XML/1998/namespace",
}

XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


@dataclass
class SourceRef:
    equation_id: str | None = None
    math_id: str | None = None
    tex: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        if self.equation_id is not None:
            payload["equation_id"] = self.equation_id
        if self.math_id is not None:
            payload["math_id"] = self.math_id
        if self.tex is not None:
            payload["tex"] = self.tex
        return payload


@dataclass
class MathUnit:
    unit_id: str
    source_ref: SourceRef
    text: str | None
    contentml: etree._Element | None
    order_index: int


def load_tree(xml_path: str | Path) -> etree._ElementTree:
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(str(xml_path), parser)


def extract_math_unit(equation: etree._Element, order_index: int) -> MathUnit | None:
    math_node = equation.find(".//ltx:Math", namespaces=NS)
    if math_node is None:
        return None

    return MathUnit(
        unit_id=f"UNIT_{order_index}",
        source_ref=SourceRef(
            equation_id=equation.get(XML_ID),
            math_id=math_node.get(XML_ID),
            tex=math_node.get("tex"),
        ),
        text=math_node.get("text"),
        contentml=math_node.find("m:math", namespaces=NS),
        order_index=order_index,
    )


def load_combined_file(xml_path: str | Path) -> list[MathUnit]:
    tree = load_tree(xml_path)
    root = tree.getroot()

    units: list[MathUnit] = []
    for order_index, equation in enumerate(root.findall(".//ltx:equation", namespaces=NS)):
        unit = extract_math_unit(equation, order_index=order_index)
        if unit is not None:
            units.append(unit)
    return units


def iter_combined_files(directory: str | Path) -> Iterator[Path]:
    base = Path(directory)
    for path in sorted(base.glob("*.xml")):
        yield path


def load_combined_directory(directory: str | Path) -> list[MathUnit]:
    units: list[MathUnit] = []
    for path in iter_combined_files(directory):
        units.extend(load_combined_file(path))
    return units
