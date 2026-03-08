from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

# Optional PDF export (reportlab)
try:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False


DEFAULT_SCHEMA: Dict[str, Any] = {
    "project_name": "",
    "problem_statement": "",
    "target_users": [],
    "goals": [],
    "non_goals": [],
    "functional_requirements": [],
    "non_functional_requirements": {
        "performance": "",
        "security": "",
        "scalability": "",
        "availability": ""
    },
    "core_entities": [],
    "assumptions": [],
    "constraints": [],
    "open_questions": []
}


@dataclass
class ArtefactPaths:
    input_json: Path
    output_dir: Path


class ArtefactsAgentExecutor:
    """
    Reads requirements JSON and generates project artefacts (md/pdf).
    """

    def __init__(self, input_json: str | Path = "outputs/requirements_output.json",
                 output_dir: str | Path = "outputs") -> None:
        self.paths = ArtefactPaths(
            input_json=Path(input_json),
            output_dir=Path(output_dir)
        )
        self.paths.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, export_pdf: bool = False) -> Dict[str, Path]:
        data = self._load_and_normalize(self.paths.input_json)

        artefacts = {
            "requirements_summary.md": self.generate_requirements_summary(data),
            "user_stories.md": self.generate_user_stories(data),
            "scope_constraints.md": self.generate_scope_constraints(data),
        }

        saved: Dict[str, Path] = {}
        for filename, content in artefacts.items():
            path = self._save_text(filename, content)
            saved[filename] = path

        # graceful fallback if reportlab missing
        if export_pdf and not REPORTLAB_AVAILABLE:
            print("[WARN] reportlab is not installed. Skipping PDF export.")
            export_pdf = False

        if export_pdf:
            for _, md_path in list(saved.items()):
                if md_path.suffix.lower() == ".md":
                    pdf_name = md_path.stem + ".pdf"
                    pdf_path = self.paths.output_dir / pdf_name
                    self._export_text_to_pdf(md_path.read_text(encoding="utf-8"), pdf_path)
                    saved[pdf_name] = pdf_path

        return saved

    # ----------------------------
    # Loading / Validation
    # ----------------------------
    def _load_and_normalize(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Input JSON not found: {path}")

        raw = path.read_text(encoding="utf-8").strip()
        data = self._parse_json_loose(raw)
        return self._normalize(data)

    def _parse_json_loose(self, raw: str) -> Dict[str, Any]:
        text = raw.strip()

        # strip markdown code fences if present
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].strip() == "```":
                text = "\n".join(lines[1:-1]).strip()
                if text.lower().startswith("json"):
                    text = text[4:].strip()

        # extract JSON object if extra text exists
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]

        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("Top-level JSON must be an object.")
        return parsed

    def _normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = json.loads(json.dumps(DEFAULT_SCHEMA))  # deep copy

        for key in normalized.keys():
            if key in data:
                normalized[key] = data[key]

        # string fields
        for key in ["project_name", "problem_statement"]:
            v = normalized.get(key, "")
            normalized[key] = "" if v is None else str(v)

        # list fields
        list_fields = [
            "target_users", "goals", "non_goals", "functional_requirements",
            "core_entities", "assumptions", "constraints", "open_questions"
        ]
        for key in list_fields:
            v = normalized.get(key, [])
            if isinstance(v, list):
                normalized[key] = [str(x) for x in v if x is not None]
            elif v in (None, ""):
                normalized[key] = []
            else:
                normalized[key] = [str(v)]

        # nfr fields
        nfr_default = DEFAULT_SCHEMA["non_functional_requirements"]
        nfr = normalized.get("non_functional_requirements", {})
        if not isinstance(nfr, dict):
            nfr = {}
        fixed_nfr = {}
        for k in nfr_default.keys():
            val = nfr.get(k, "")
            fixed_nfr[k] = "" if val is None else str(val)
        normalized["non_functional_requirements"] = fixed_nfr

        return normalized

    # ----------------------------
    # Artefact generators
    # ----------------------------
    def generate_requirements_summary(self, data: Dict[str, Any]) -> str:
        nfr = data.get("non_functional_requirements", {})

        lines: List[str] = []
        lines.append(f"# Requirements Summary: {data.get('project_name', '')}")
        lines.append("")
        lines.append("## Problem Statement")
        lines.append(data.get("problem_statement", "") or "N/A")
        lines.append("")

        lines.append("## Target Users")
        lines.extend(self._bullet_list(data.get("target_users", [])))
        lines.append("")

        lines.append("## Goals")
        lines.extend(self._bullet_list(data.get("goals", [])))
        lines.append("")

        lines.append("## Non-Goals")
        lines.extend(self._bullet_list(data.get("non_goals", [])))
        lines.append("")

        lines.append("## Functional Requirements")
        frs = data.get("functional_requirements", [])
        if frs:
            for i, fr in enumerate(frs, start=1):
                lines.append(f"{i}. {fr}")
        else:
            lines.append("1. N/A")
        lines.append("")

        lines.append("## Non-Functional Requirements")
        lines.append(f"- Performance: {nfr.get('performance', '') or 'N/A'}")
        lines.append(f"- Security: {nfr.get('security', '') or 'N/A'}")
        lines.append(f"- Scalability: {nfr.get('scalability', '') or 'N/A'}")
        lines.append(f"- Availability: {nfr.get('availability', '') or 'N/A'}")
        lines.append("")

        lines.append("## Core Entities")
        lines.extend(self._bullet_list(data.get("core_entities", [])))
        lines.append("")

        lines.append("## Open Questions")
        lines.extend(self._bullet_list(data.get("open_questions", [])))
        lines.append("")

        return "\n".join(lines)

    def generate_user_stories(self, data: Dict[str, Any]) -> str:
        users = data.get("target_users", [])
        goals = data.get("goals", [])
        frs = data.get("functional_requirements", [])
        constraints = data.get("constraints", [])

        role = self._pick_role(users)
        benefit = goals[0] if goals else "achieve the intended project outcome"

        lines: List[str] = []
        lines.append(f"# User Stories: {data.get('project_name', '')}")
        lines.append("")
        lines.append("> Auto-generated from the Requirements Agent JSON output.")
        lines.append("")

        if not frs:
            lines.append("- No functional requirements were provided.")
            lines.append("")
            return "\n".join(lines)

        for idx, fr in enumerate(frs, start=1):
            story_text = self._fr_to_user_story(role, fr, benefit)

            lines.append(f"## US-{idx:02d}")
            lines.append(story_text)
            lines.append("")
            lines.append("### Acceptance Criteria")
            lines.append("- The functionality is clearly defined and testable.")
            lines.append("- The feature aligns with project goals and scope.")
            if constraints:
                lines.append("- The implementation respects the documented constraints.")
            lines.append("- The output can be reviewed and revised by the user/team.")
            lines.append("")

        return "\n".join(lines)

    def generate_scope_constraints(self, data: Dict[str, Any]) -> str:
        lines: List[str] = []
        lines.append(f"# Scope & Constraints: {data.get('project_name', '')}")
        lines.append("")

        lines.append("## In Scope (Goals)")
        lines.extend(self._bullet_list(data.get("goals", [])))
        lines.append("")

        lines.append("## Out of Scope (Non-Goals)")
        lines.extend(self._bullet_list(data.get("non_goals", [])))
        lines.append("")

        lines.append("## Assumptions")
        lines.extend(self._bullet_list(data.get("assumptions", [])))
        lines.append("")

        lines.append("## Constraints")
        lines.extend(self._bullet_list(data.get("constraints", [])))
        lines.append("")

        lines.append("## Core Entities")
        lines.extend(self._bullet_list(data.get("core_entities", [])))
        lines.append("")

        return "\n".join(lines)

    # ----------------------------
    # Helpers
    # ----------------------------
    def _save_text(self, filename: str, content: str) -> Path:
        path = self.paths.output_dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    def _bullet_list(self, items: List[str]) -> List[str]:
        if not items:
            return ["- N/A"]
        return [f"- {item}" for item in items]

    def _pick_role(self, users: List[str]) -> str:
        return users[0] if users else "user"

    def _fr_to_user_story(self, role: str, fr: str, benefit: str) -> str:
        fr_clean = (fr or "").strip()
        if not fr_clean:
            fr_clean = "use the system"
        if fr_clean and fr_clean[0].isupper():
            fr_clean = fr_clean[0].lower() + fr_clean[1:]
        return f"As a {role}, I want to {fr_clean} so that I can {benefit.lower()}."

    def _export_text_to_pdf(self, text: str, pdf_path: Path) -> None:
        c = canvas.Canvas(str(pdf_path), pagesize=LETTER)
        width, height = LETTER

        left_margin = 0.8 * inch
        top_margin = 0.8 * inch
        line_height = 14
        y = height - top_margin

        c.setFont("Helvetica", 11)

        max_chars = 95
        for raw_line in text.splitlines():
            wrapped_lines = self._wrap_line(raw_line, max_chars=max_chars)
            for line in wrapped_lines:
                if y < 0.8 * inch:
                    c.showPage()
                    c.setFont("Helvetica", 11)
                    y = height - top_margin
                c.drawString(left_margin, y, line)
                y -= line_height

        c.save()

    def _wrap_line(self, line: str, max_chars: int = 95) -> List[str]:
        if len(line) <= max_chars:
            return [line]
        out = []
        current = line
        while len(current) > max_chars:
            cut = current.rfind(" ", 0, max_chars)
            if cut == -1:
                cut = max_chars
            out.append(current[:cut].rstrip())
            current = current[cut:].lstrip()
        if current:
            out.append(current)
        return out