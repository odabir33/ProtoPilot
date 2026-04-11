from __future__ import annotations

import json
from typing import Any

from orchestration.store import Stage, get_or_create_project


def _log_tool_event(tool: str, payload: dict[str, Any]) -> None:
    print(f"[TOOL_CALL] {tool} {json.dumps(payload, ensure_ascii=False)}")


def submit_spec(project_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    """
    Save finalized requirements spec and move project to non-technical artifacts.
    """
    proj = get_or_create_project(project_id, req_session_id=project_id)
    before = proj.stage.value
    proj.spec = spec
    proj.stage = Stage.ARTIFACTS_NON_TECH
    _log_tool_event(
        "submit_spec",
        {
            "project_id": project_id,
            "stage_before": before,
            "stage_after": proj.stage.value,
            "spec_keys": list(spec.keys()),
        },
    )
    return {"ok": True, "project_id": project_id, "stage": proj.stage.value}


def load_spec(project_id: str) -> dict[str, Any]:
    """
    Load requirements spec for artifact generation.
    """
    proj = get_or_create_project(project_id, req_session_id=project_id)
    _log_tool_event(
        "load_spec",
        {
            "project_id": project_id,
            "stage": proj.stage.value,
            "has_spec": proj.spec is not None,
        },
    )
    return {"project_id": project_id, "spec": proj.spec or {}}


def save_nontech_artifacts(project_id: str, artifacts_md: str) -> dict[str, Any]:
    """
    Save non-technical artifacts and wait for product-manager approval.
    """
    proj = get_or_create_project(project_id, req_session_id=project_id)
    before = proj.stage.value
    proj.nontech_artifacts_md = artifacts_md
    proj.stage = Stage.WAIT_APPROVAL
    _log_tool_event(
        "save_nontech_artifacts",
        {
            "project_id": project_id,
            "stage_before": before,
            "stage_after": proj.stage.value,
            "artifacts_len": len(artifacts_md or ""),
        },
    )
    return {"ok": True, "project_id": project_id, "stage": proj.stage.value}


def save_technical_artifacts(project_id: str, artifacts_md: str) -> dict[str, Any]:
    """
    Save technical artifacts and move workflow to CODEGEN.
    """
    proj = get_or_create_project(project_id, req_session_id=project_id)
    before = proj.stage.value
    proj.technical_artifacts_md = artifacts_md
    proj.stage = Stage.CODEGEN
    _log_tool_event(
        "save_technical_artifacts",
        {
            "project_id": project_id,
            "stage_before": before,
            "stage_after": proj.stage.value,
            "artifacts_len": len(artifacts_md or ""),
        },
    )
    return {"ok": True, "project_id": project_id, "stage": proj.stage.value}


def save_backend_code(project_id: str, files: dict[str, str]) -> dict[str, Any]:
    """
    Save generated Spring Boot backend source files.
    files is a dict mapping file path to file content (e.g. "backend/pom.xml": "...").
    Does NOT advance stage — call save_frontend_code to complete code generation.
    """
    proj = get_or_create_project(project_id, req_session_id=project_id)
    proj.generated_code_files = files
    _log_tool_event(
        "save_backend_code",
        {"project_id": project_id, "files": list(files.keys())},
    )
    return {"ok": True, "project_id": project_id, "files_saved": len(files)}


def save_frontend_code(project_id: str, files: dict[str, str]) -> dict[str, Any]:
    """
    Save generated Angular frontend source files and advance the project to DEPLOY stage.
    files is a dict mapping file path to file content (e.g. "frontend/src/main.ts": "...").
    Merges with previously saved backend files.
    """
    proj = get_or_create_project(project_id, req_session_id=project_id)
    before = proj.stage.value
    merged = {**(proj.generated_code_files or {}), **files}
    proj.generated_code_files = merged
    proj.stage = Stage.DEPLOY
    _log_tool_event(
        "save_frontend_code",
        {
            "project_id": project_id,
            "stage_before": before,
            "stage_after": proj.stage.value,
            "files": list(files.keys()),
            "total_files": len(merged),
        },
    )
    return {"ok": True, "project_id": project_id, "stage": proj.stage.value, "total_files_saved": len(merged)}


def set_project_stage(project_id: str, stage: str) -> dict[str, Any]:
    """
    Force-set project stage. Intended for explicit orchestration transitions.
    """
    proj = get_or_create_project(project_id, req_session_id=project_id)
    before = proj.stage.value
    proj.stage = Stage(stage)
    _log_tool_event(
        "set_project_stage",
        {
            "project_id": project_id,
            "stage_before": before,
            "stage_after": proj.stage.value,
        },
    )
    return {"ok": True, "project_id": project_id, "stage": proj.stage.value}
