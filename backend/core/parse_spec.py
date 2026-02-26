import json
import re
from typing import Any, Optional

_JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)

def extract_json_block(text: str) -> Optional[dict[str, Any]]:
    
    m = _JSON_BLOCK_RE.search(text)
    if not m:
        return None
    raw = m.group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None

def infer_done(text: str, spec: Optional[dict[str, Any]]) -> bool:
    if spec is not None:
        return True
    if "requirements are now sufficiently clear" in text.lower():
        return True
    return False