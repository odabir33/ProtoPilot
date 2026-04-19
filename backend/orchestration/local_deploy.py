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

    # Clean previous deploy but preserve node_modules to avoid reinstalling deps
    _CACHE_DIR = Path(tempfile.gettempdir()) / "protopilot_node_modules_cache"
    _CACHE_PKG = Path(tempfile.gettempdir()) / "protopilot_node_modules_cache_pkg.json"

    # Decide whether the cached node_modules are still valid for this package.json
    new_pkg_content = files.get("frontend/package.json", "")
    cached_pkg_content = _CACHE_PKG.read_text() if _CACHE_PKG.exists() else ""
    cache_valid = bool(_CACHE_DIR.exists() and new_pkg_content == cached_pkg_content)

    if _DEPLOY_DIR.exists():
        node_modules = _DEPLOY_DIR / "frontend" / "node_modules"
        if node_modules.exists() and cache_valid:
            # Stash current node_modules only if they match the new package.json
            if _CACHE_DIR.exists():
                shutil.rmtree(_CACHE_DIR)
            shutil.move(str(node_modules), str(_CACHE_DIR))
        elif _CACHE_DIR.exists() and not cache_valid:
            # package.json changed — discard stale cache
            print("[DEPLOY] package.json changed, discarding node_modules cache")
            shutil.rmtree(_CACHE_DIR)
            _CACHE_PKG.unlink(missing_ok=True)
        shutil.rmtree(_DEPLOY_DIR)
    _DEPLOY_DIR.mkdir(parents=True)

    # Validate required frontend entry-point files exist before writing anything.
    _REQUIRED_FRONTEND = [
        "frontend/src/main.ts",
        "frontend/angular.json",
        "frontend/tsconfig.app.json",
        "frontend/src/index.html",
        "frontend/package.json",
    ]
    missing = [f for f in _REQUIRED_FRONTEND if f not in files]
    if missing:
        saved = sorted(f for f in files if f.startswith("frontend/"))
        raise RuntimeError(
            f"Frontend codegen is missing required files: {missing}\n"
            f"Frontend files that were saved: {saved}"
        )

    print(f"[DEPLOY] Writing {len(files)} files to {_DEPLOY_DIR}")
    _write_files(files, _DEPLOY_DIR)

    # Restore cached node_modules if still valid
    node_modules_dest = _DEPLOY_DIR / "frontend" / "node_modules"
    if cache_valid and _CACHE_DIR.exists():
        print("[DEPLOY] Restoring cached node_modules...")
        shutil.move(str(_CACHE_DIR), str(node_modules_dest))

    backend_dir = _DEPLOY_DIR / "backend"
    frontend_dir = _DEPLOY_DIR / "frontend"

    # Kill previous processes if any
    for proc in [_backend_proc, _frontend_proc]:
        if proc and proc.poll() is None:
            proc.terminate()

    # Kill any stale processes still holding the ports
    for port in [8080, 4200]:
        pids = subprocess.run(["lsof", "-ti", f"tcp:{port}"], capture_output=True, text=True).stdout.strip().split()
        if pids:
            subprocess.run(["kill", "-9"] + pids, capture_output=True)
            print(f"[DEPLOY] Killed stale process(es) on port {port}: {pids}")

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
    for attempt in range(75):
        await asyncio.sleep(2)
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
    subprocess.run(
        ["npm", "install", "--legacy-peer-deps"],
        cwd=frontend_dir,
        check=True,
    )
    # Cache node_modules for next deploy (save package.json fingerprint)
    _CACHE_PKG.write_text(new_pkg_content)

    print("[DEPLOY] Starting Angular frontend...")
    _frontend_proc = subprocess.Popen(
        ["./node_modules/.bin/ng", "serve", "--proxy-config", "proxy.conf.json"],
        cwd=frontend_dir,
        stdout=open(_DEPLOY_DIR / "frontend.log", "w"),
        stderr=subprocess.STDOUT,
    )

    # Wait for frontend
    print("[DEPLOY] Waiting for frontend...")
    for attempt in range(60):
        await asyncio.sleep(2)
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
