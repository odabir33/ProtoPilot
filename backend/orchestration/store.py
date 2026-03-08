from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

class Stage(str, Enum):
    REQ = "REQ"
    ARTIFACTS_NON_TECH = "ARTIFACTS_NON_TECH"
    WAIT_APPROVAL = "WAIT_APPROVAL"
    TECH_ARTIFACTS = "TECH_ARTIFACTS"
    CODEGEN = "CODEGEN"
    QA = "QA"

@dataclass
class ProjectState:
    project_id: str
    req_session_id: str
    stage: Stage = Stage.REQ
    spec: Optional[dict[str, Any]] = None
    nontech_artifacts_md: Optional[str] = None
    technical_artifacts_md: Optional[str] = None

_PROJECTS: dict[str, ProjectState] = {}

def get_or_create_project(project_id: str, req_session_id: str) -> ProjectState:
    proj = _PROJECTS.get(project_id)
    if proj is None:
        proj = ProjectState(project_id=project_id, req_session_id=req_session_id)
        _PROJECTS[project_id] = proj
    return proj
