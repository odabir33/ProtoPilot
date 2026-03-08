import re

# recognize quesitons
_ENUM_Q_RE = re.compile(
    r"(?m)^\s*(\d+)[\.\)\、]\s+(.*?)(?=\n\s*\d+[\.\)\、]\s+|\Z)",
    re.DOTALL,
)

_BULLET_LINE_RE = re.compile(r"(?m)^\s*[-•]\s+(.*)$")


def extract_questions(text: str) -> list[dict[str, str]]:
    """
    Extract questions from model reply, return:
      [{"id": "Q1", "text": "..."}, ...]
    Priorities:
      1) Numbered blocks (1. / 2) / 3、)
      2) Bullet lines that look like questions (ending with ?)
    """
    questions: list[str] = []

    # 1) numbered blocks
    matches = list(_ENUM_Q_RE.finditer(text))
    if matches:
        for m in matches:
            q = m.group(2).strip()
            q = _cleanup_question_text(q)
            if q:
                questions.append(q)

    # 2) fallback: bullet lines
    if not questions:
        for m in _BULLET_LINE_RE.finditer(text):
            line = m.group(1).strip()
            line = _cleanup_question_text(line)
            if line.endswith("?") and len(line) > 3:
                questions.append(line)

    # Build Q1/Q2...
    out: list[dict[str, str]] = []
    for i, q in enumerate(questions, start=1):
        out.append({"id": f"Q{i}", "text": q})
    return out


def _cleanup_question_text(q: str) -> str:
    # delete Markdown symbols
    q = re.sub(r"\*\*(.*?)\*\*", r"\1", q)
    q = re.sub(r"(?m)^\s*[\*\-•]\s+", "", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q
