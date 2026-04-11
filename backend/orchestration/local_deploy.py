from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from orchestration.store import Stage, get_or_create_project

logger = logging.getLogger(__name__)

# Reuse a fixed temp dir per run so restarts don't leak processes
_DEPLOY_DIR = Path(tempfile.gettempdir()) / "protopilot_deploy"

_backend_proc: subprocess.Popen | None = None
_frontend_proc: subprocess.Popen | None = None


def _write_files(files: dict[str, str], base_dir: Path) -> None:
    for rel_path, content in files.items():
        dest = base_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        print(f"[DEPLOY] wrote {rel_path}")


async def deploy_locally(project_id: str) -> str:
    """
    Write generated files to a temp dir, start Spring Boot + Angular locally.
    Returns http://localhost:4200
    """
    global _backend_proc, _frontend_proc

    proj = get_or_create_project(project_id, req_session_id=project_id)
    files = proj.generated_code_files or {}
    if not files:
        raise RuntimeError("No generated_code_files found for project")

    # Clean previous deploy
    if _DEPLOY_DIR.exists():
        shutil.rmtree(_DEPLOY_DIR)
    _DEPLOY_DIR.mkdir(parents=True)

    print(f"[DEPLOY] Writing {len(files)} files to {_DEPLOY_DIR}")
    _write_files(files, _DEPLOY_DIR)

    backend_dir = _DEPLOY_DIR / "backend"
    frontend_dir = _DEPLOY_DIR / "frontend"

    # Kill previous processes if any
    for proc in [_backend_proc, _frontend_proc]:
        if proc and proc.poll() is None:
            proc.terminate()

    # Start Spring Boot
    print("[DEPLOY] Starting Spring Boot backend...")
    java_env = {**os.environ, "JAVA_HOME": "/opt/homebrew/opt/openjdk@17"}
    _backend_proc = subprocess.Popen(
        ["mvn", "spring-boot:run"],
        cwd=backend_dir,
        env=java_env,
        stdout=open(_DEPLOY_DIR / "backend.log", "w"),
        stderr=subprocess.STDOUT,
    )

    # Wait for backend health
    print("[DEPLOY] Waiting for backend health...")
    for attempt in range(30):
        await asyncio.sleep(5)
        result = subprocess.run(
            ["curl", "-sf", "http://localhost:8080/actuator/health"],
            capture_output=True,
        )
        if result.returncode == 0:
            print(f"[DEPLOY] Backend healthy after {attempt + 1} attempts")
            break
    else:
        log = (_DEPLOY_DIR / "backend.log").read_text()[-2000:]
        raise RuntimeError(f"Backend failed to start.\n\nLast logs:\n{log}")

    # npm install + start Angular
    print("[DEPLOY] Installing frontend deps...")
    subprocess.run(["npm", "install", "--silent"], cwd=frontend_dir, check=True)

    print("[DEPLOY] Starting Angular frontend...")
    _frontend_proc = subprocess.Popen(
        ["ng", "serve", "--proxy-config", "proxy.conf.json"],
        cwd=frontend_dir,
        stdout=open(_DEPLOY_DIR / "frontend.log", "w"),
        stderr=subprocess.STDOUT,
    )

    # Wait for frontend
    print("[DEPLOY] Waiting for frontend...")
    for attempt in range(24):
        await asyncio.sleep(5)
        result = subprocess.run(
            ["curl", "-sf", "http://localhost:4200"],
            capture_output=True,
        )
        if result.returncode == 0:
            print(f"[DEPLOY] Frontend ready after {attempt + 1} attempts")
            break
    else:
        log = (_DEPLOY_DIR / "frontend.log").read_text()[-2000:]
        raise RuntimeError(f"Frontend failed to start.\n\nLast logs:\n{log}")

    proj.preview_url = "http://localhost:4200"
    proj.stage = Stage.QA
    print(f"[DEPLOY] Done. Open http://localhost:4200")
    return "http://localhost:4200"
