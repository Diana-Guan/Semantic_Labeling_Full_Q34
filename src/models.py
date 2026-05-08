from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ASTNode:
    kind: str
    value: str | None = None
    children: list["ASTNode"] | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"kind": self.kind}
        if self.value is not None:
            payload["value"] = self.value
        payload["children"] = [child.to_dict() for child in self.children or []]
        return payload


@dataclass
class Label:
    id: str
    evidence: list[str]

    def to_dict(self) -> dict[str, object]:
        return {"id": self.id, "evidence": self.evidence}


@dataclass
class StepRecord:
    step_id: str
    source_equation_id: str
    description: str
    ast: ASTNode
    structural_labels: list[str]
    step_labels: list[Label]
    source_math_id: str | None = None
    raw_text: str | None = None
    cue_text: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "step_id": self.step_id,
            "source_equation_id": self.source_equation_id,
            "description": self.description,
            "ast": self.ast.to_dict(),
            "structural_labels": self.structural_labels,
            "step_labels": [label.to_dict() for label in self.step_labels],
        }
        if self.source_math_id is not None:
            payload["source_math_id"] = self.source_math_id
        if self.raw_text is not None:
            payload["raw_text"] = self.raw_text
        if self.cue_text is not None:
            payload["cue_text"] = self.cue_text
        return payload
