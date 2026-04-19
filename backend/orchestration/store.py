from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class Stage(str, Enum):
    REQ = "REQ"
    ARTIFACTS_NON_TECH = "ARTIFACTS_NON_TECH"
    WAIT_APPROVAL = "WAIT_APPROVAL"
    TECH_ARTIFACTS = "TECH_ARTIFACTS"
    CODEGEN = "CODEGEN"
    DEPLOY = "DEPLOY"
    QA = "QA"


@dataclass
class ProjectState:
    project_id: str
    req_session_id: str
    stage: Stage = Stage.REQ
    spec: Optional[dict[str, Any]] = None
    nontech_artifacts_md: Optional[str] = None
    technical_artifacts_md: Optional[str] = None
    generated_code_files: Optional[dict[str, str]] = None
    preview_url: Optional[str] = None
    api_spec_summary: Optional[str] = None  # compact plain-text endpoint list for frontend agent


_PROJECTS: dict[str, ProjectState] = {}
_JOBS: dict[str, dict] = {}


def create_job(job_id: str):
    _JOBS[job_id] = {"status": "running", "result": None, "error": None}

def finish_job(job_id: str, result: dict):
    _JOBS[job_id] = {"status": "done", "result": result, "error": None}

def fail_job(job_id: str, error: str):
    _JOBS[job_id] = {"status": "failed", "result": None, "error": error}

def get_job(job_id: str) -> dict | None:
    return _JOBS.get(job_id)


def get_or_create_project(project_id: str, req_session_id: str) -> ProjectState:
    proj = _PROJECTS.get(project_id)
    if proj is None:
        proj = ProjectState(project_id=project_id, req_session_id=req_session_id)
        _PROJECTS[project_id] = proj
    return proj
