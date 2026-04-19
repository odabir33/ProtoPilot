import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from core.auth import get_oauth_token
from core.llm import create_litellm
from core.runner import run_turn
from agents.registry import AGENT_FACTORIES
from orchestration.tools import (
    load_spec,
    get_api_spec,
    save_nontech_artifacts,
    save_technical_artifacts,
    save_backend_code,
    save_frontend_code,
    set_project_stage,
    submit_spec,
)
from orchestration.local_deploy import deploy_locally
from orchestration.store import Stage, get_or_create_project, create_job, finish_job, fail_job

logger = logging.getLogger(__name__)


class Orchestrator:
    def _build_response(self, proj, reply: str, artifacts_md: str | None = None, job_id: str | None = None) -> dict[str, Any]:
        return {
            "stage": proj.stage,
            "reply": reply,
            "spec": proj.spec,
            "nontech_artifacts_md": proj.nontech_artifacts_md,
            "technical_artifacts_md": proj.technical_artifacts_md,
            "artifacts_md": artifacts_md or proj.technical_artifacts_md or proj.nontech_artifacts_md,
            "preview_url": proj.preview_url,
            "job_id": job_id,
        }

    def _requirements_tools(self) -> list:
        return [submit_spec, set_project_stage]

    def _artifacts_tools(self) -> list:
        return [load_spec, save_nontech_artifacts, save_technical_artifacts, set_project_stage]

    def _backend_codegen_tools(self) -> list:
        return [save_backend_code]

    def _frontend_codegen_tools(self) -> list:
        return [get_api_spec, save_frontend_code]

    async def _extract_openapi_spec(self, files: dict[str, str]) -> str | None:
        """
        Write backend files to a temp dir, start Spring Boot, fetch /v3/api-docs, then kill the process.
        Returns the OpenAPI spec as a JSON string, or None if extraction fails.
        """
        spec_dir = Path(tempfile.gettempdir()) / "protopilot_spec_extract"
        proc = None
        try:
            if spec_dir.exists():
                shutil.rmtree(spec_dir)
            spec_dir.mkdir(parents=True)

            # Write only backend files
            for rel_path, content in files.items():
                if rel_path.startswith("backend/"):
                    dest = spec_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding="utf-8")

            java_env = {**os.environ, "JAVA_HOME": "/opt/homebrew/opt/openjdk@17"}
            log_path = spec_dir / "spec_extract.log"
            log_file = open(log_path, "w")
            proc = subprocess.Popen(
                ["mvn", "spring-boot:run"],
                cwd=spec_dir / "backend",
                env=java_env,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )

            # Wait for backend health
            logger.info("Waiting for backend to start for OpenAPI spec extraction...")
            for attempt in range(60):
                await asyncio.sleep(2)
                try:
                    result = subprocess.run(
                        ["curl", "-sf", "http://localhost:8080/actuator/health"],
                        capture_output=True, timeout=3,
                    )
                    if result.returncode == 0:
                        logger.info("Backend healthy after %d attempts, fetching spec...", attempt + 1)
                        break
                except Exception:
                    pass
            else:
                logger.warning("Backend did not start in time for spec extraction")
                return None

            # Fetch OpenAPI spec
            result = subprocess.run(
                ["curl", "-sf", "http://localhost:8080/v3/api-docs"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0 or not result.stdout.strip():
                logger.warning("Failed to fetch OpenAPI spec: %s", result.stderr)
                return None

            spec = json.loads(result.stdout)
            logger.info("OpenAPI spec extracted: %d paths", len(spec.get("paths", {})))
            return json.dumps(spec, indent=2)

        except Exception as e:
            logger.error("OpenAPI spec extraction failed: %s", e, exc_info=True)
            return None
        finally:
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
            try:
                log_file.close()
            except Exception:
                pass
            # Kill anything still on 8080
            pids = subprocess.run(["lsof", "-ti", "tcp:8080"], capture_output=True, text=True).stdout.strip().split()
            if pids:
                subprocess.run(["kill", "-9"] + pids, capture_output=True)

    async def _handle_wait_approval(self, project_id: str, req_session_id: str, normalized: str) -> dict[str, Any]:
        proj = get_or_create_project(project_id, req_session_id)
        if normalized == "approve":
            set_project_stage(project_id, Stage.TECH_ARTIFACTS.value)
            return {}
        if normalized == "change":
            set_project_stage(project_id, Stage.REQ.value)
            proj = get_or_create_project(project_id, req_session_id)
            return self._build_response(
                proj=proj,
                reply="You have entered revision mode. Please enter the points to be modified.",
                artifacts_md=proj.nontech_artifacts_md,
            )
        return self._build_response(
            proj=proj,
            reply="approve or change",
            artifacts_md=proj.nontech_artifacts_md,
        )

    async def _run_requirements(self, token: str, project_id: str, req_session_id: str, user_message: str) -> dict[str, Any]:
        proj = get_or_create_project(project_id, req_session_id)
        llm = create_litellm(token, model="gemini-2.5-flash-litellm-usw1")
        req_agent = AGENT_FACTORIES["requirements"](llm, tools=self._requirements_tools())
        phase = "requirements_revision" if proj.nontech_artifacts_md else "requirements_gathering"
        req_prompt = (
            f"project_id={project_id}\n"
            f"phase={phase}\n"
            "Continue requirements gathering for this project.\n"
            f"User message:\n{user_message}"
        )
        logger.info("Calling run_turn for requirements agent...")
        reply = await run_turn(req_agent, session_id=proj.req_session_id, message=req_prompt)
        logger.info("run_turn returned: %s", reply[:100] if reply else "(empty)")
        proj = get_or_create_project(project_id, req_session_id)

        if proj.stage == Stage.ARTIFACTS_NON_TECH and proj.spec:
            return await self._run_artifacts_non_tech(token, project_id, req_session_id)

        return self._build_response(proj=proj, reply=reply)

    async def handle(self, project_id: str, req_session_id: str, user_message: str) -> dict:
        proj = get_or_create_project(project_id, req_session_id)
        normalized = user_message.strip().lower()

        # Approval gate does not need an LLM call.
        if proj.stage == Stage.WAIT_APPROVAL:
            approval_result = await self._handle_wait_approval(project_id, req_session_id, normalized)
            if approval_result:
                return approval_result
            proj = get_or_create_project(project_id, req_session_id)

        # Remaining stages are model-backed.
        logger.info("Fetching OAuth token...")
        token = await get_oauth_token()
        logger.info("OAuth token OK. Stage=%s", proj.stage)

        if proj.stage == Stage.REQ:
            logger.info("Running requirements agent...")
            return await self._run_requirements(token, project_id, req_session_id, user_message)
        if proj.stage == Stage.ARTIFACTS_NON_TECH:
            return await self._run_artifacts_non_tech(token, project_id, req_session_id)
        if proj.stage == Stage.TECH_ARTIFACTS:
            return await self._run_artifacts_technical(token, project_id, req_session_id)

        if proj.stage == Stage.CODEGEN:
            return await self._start_codegen_job(token, project_id, req_session_id)
        if proj.stage == Stage.DEPLOY:
            return await self._start_deploy_job(project_id, req_session_id)

        return self._build_response(
            proj=proj,
            reply="Pipeline complete.",
        )

    async def _start_codegen_job(self, token: str, project_id: str, req_session_id: str) -> dict:
        job_id = f"{project_id}-codegen-{uuid.uuid4().hex[:8]}"
        create_job(job_id)

        async def _run():
            try:
                result = await self._run_codegen(token, project_id, req_session_id)
                finish_job(job_id, result)
            except Exception as e:
                fail_job(job_id, str(e))

        asyncio.create_task(_run())
        return {"stage": "CODEGEN_PENDING", "job_id": job_id, "reply": "Code generation started.", "preview_url": None}

    async def _run_codegen(self, token: str, project_id: str, req_session_id: str) -> dict:
        llm_pro = create_litellm(token, model="gemini-2.5-pro-litellm-usw1")
        proj = get_or_create_project(project_id, req_session_id)

        artifacts_section = [
            "",
            "## Technical artifacts",
            proj.technical_artifacts_md or "(not available)",
        ]

        # Backend: single batch — generate all files (entities, repos, services, controllers) at once.
        backend_prompt = "\n".join([
            f"project_id={project_id}",
        ] + artifacts_section)
        logger.info("Backend codegen starting...")
        try:
            b_reply = await run_turn(
                AGENT_FACTORIES["codegen_backend"](llm_pro, tools=self._backend_codegen_tools()),
                session_id=f"{req_session_id}-codegen-backend",
                message=backend_prompt,
            )
            logger.info("Backend codegen reply: %s", (b_reply or "")[:500])
        except Exception as e:
            logger.error("Backend codegen exception: %s", e, exc_info=True)
        proj = get_or_create_project(project_id, req_session_id)
        logger.info("Backend codegen done. total_files=%d files=%s", len(proj.generated_code_files or {}), list((proj.generated_code_files or {}).keys()))

        # Extract OpenAPI spec and store as-is for tool-based access by the frontend agent.
        # Full JSON is returned via get_api_spec() tool — no summarization, no accuracy loss.
        # WAF is not a concern here because the spec travels via tool response, not request body.
        logger.info("Extracting OpenAPI spec from backend...")
        openapi_spec = await self._extract_openapi_spec(proj.generated_code_files or {})
        if openapi_spec:
            proj.api_spec_summary = openapi_spec
            logger.info("OpenAPI spec stored (%d chars)", len(openapi_spec))
        else:
            # Fallback: parse controller annotations + DTO fields when Spring Boot fails to start.
            logger.warning("OpenAPI spec extraction failed, building fallback from annotations")
            lines = ["API endpoints (inferred from generated controllers):"]
            files = proj.generated_code_files or {}
            # Collect DTO fields: map simple class name → [field names]
            dto_fields: dict[str, list[str]] = {}
            for path, content in files.items():
                if not path.endswith(".java"):
                    continue
                cls_match = re.search(r'(?:class|record)\s+(\w+Dto)\b', content)
                if cls_match:
                    fields = re.findall(r'(?:private|public)\s+\S+\s+(\w+)\s*;', content)
                    dto_fields[cls_match.group(1)] = fields
            for path, content in files.items():
                if not path.endswith("Controller.java"):
                    continue
                base = re.search(r'@RequestMapping\("([^"]+)"\)', content)
                base_path = base.group(1) if base else "/api/unknown"
                for m in re.finditer(
                    r'@(GetMapping|PostMapping|PutMapping|DeleteMapping)(?:\("([^"]*)"\))?',
                    content,
                ):
                    verb = m.group(1).replace("Mapping", "").upper()
                    sub = m.group(2) or ""
                    entry = f"  {verb} {base_path}{sub}"
                    # Attach DTO fields for POST/PUT
                    if verb in ("POST", "PUT"):
                        for dto_name, fields in dto_fields.items():
                            if fields:
                                entry += f"  [body: {', '.join(fields)}]"
                                break
                    lines.append(entry)
            proj.api_spec_summary = "\n".join(lines)

        # Frontend: single batch — agent calls get_api_spec() to fetch API contract via tool.
        frontend_prompt = "\n".join([
            f"project_id={project_id}",
        ] + artifacts_section)
        logger.info("Frontend codegen starting...")
        run_id = uuid.uuid4().hex[:8]
        try:
            await run_turn(
                AGENT_FACTORIES["codegen_frontend"](llm_pro, tools=self._frontend_codegen_tools()),
                session_id=f"{req_session_id}-codegen-frontend-{run_id}",
                message=frontend_prompt,
            )
        except Exception as e:
            logger.error("Frontend codegen exception: %s", e, exc_info=True)

        proj = get_or_create_project(project_id, req_session_id)
        logger.info("Frontend codegen done. stage=%s total_files=%d", proj.stage, len(proj.generated_code_files or {}))

        if proj.stage == Stage.DEPLOY:
            return await self._start_deploy_job(project_id, req_session_id)

        return self._build_response(proj=proj, reply="Code generation did not complete.")

    async def _start_deploy_job(self, project_id: str, req_session_id: str) -> dict:
        job_id = f"{project_id}-deploy-{uuid.uuid4().hex[:8]}"
        create_job(job_id)

        async def _run():
            try:
                preview_url = await deploy_locally(project_id)
                proj = get_or_create_project(project_id, req_session_id)
                finish_job(job_id, self._build_response(proj=proj, reply=f"App deployed. Preview: {preview_url}"))
            except Exception as e:
                fail_job(job_id, str(e))

        asyncio.create_task(_run())
        return {"stage": "DEPLOY_PENDING", "job_id": job_id, "reply": "Code saved. Deploying...", "preview_url": None}

    async def _run_artifacts_non_tech(self, token: str, project_id: str, req_session_id: str) -> dict:
        llm = create_litellm(token, model="gemini-2.5-flash-litellm-usw1")
        art_agent = AGENT_FACTORIES["artifacts"](llm, tools=self._artifacts_tools(), phase="non_tech")
        art_prompt = (
            f"project_id={project_id}\n"
            "phase=non_tech\n"
            "Generate PM-facing non-technical artifacts now.\n"
            "Save full content via save_nontech_artifacts(project_id, artifacts_md), "
        )
        await run_turn(art_agent, session_id=f"{req_session_id}-nontech", message=art_prompt)
        proj = get_or_create_project(project_id, req_session_id)
        reply = (
            "Non-technical artifacts saved."
            if proj.stage == Stage.WAIT_APPROVAL
            else "Artifacts generation did not complete tool save."
        )
        return self._build_response(
            proj=proj,
            reply=reply,
            artifacts_md=proj.nontech_artifacts_md,
        )

    async def _run_artifacts_technical(self, token: str, project_id: str, req_session_id: str) -> dict:
        llm = create_litellm(token, model="gemini-2.5-pro-litellm-usw1")
        art_agent = AGENT_FACTORIES["artifacts"](llm, tools=self._artifacts_tools(), phase="technical")
        art_prompt = (
            f"project_id={project_id}\n"
            "phase=technical\n"
            "Generate technical artifacts now. "
            "Use load_spec first, then save_technical_artifacts at the end."
        )
        await run_turn(art_agent, session_id=f"{req_session_id}-tech", message=art_prompt)
        proj = get_or_create_project(project_id, req_session_id)
        if proj.stage == Stage.CODEGEN:
            return await self._start_codegen_job(token, project_id, req_session_id)
        return self._build_response(
            proj=proj,
            reply="Technical artifacts generation did not complete tool save.",
            artifacts_md=proj.technical_artifacts_md,
        )
