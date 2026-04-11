import asyncio
import logging
import uuid
from typing import Any

from core.auth import get_oauth_token
from core.llm import create_litellm

logger = logging.getLogger(__name__)
from core.runner import run_turn
from agents.registry import AGENT_FACTORIES
from orchestration.tools import (
    load_spec,
    save_nontech_artifacts,
    save_technical_artifacts,
    save_backend_code,
    save_frontend_code,
    set_project_stage,
    submit_spec,
)
from orchestration.local_deploy import deploy_locally
from orchestration.store import Stage, get_or_create_project, create_job, finish_job, fail_job


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
        return [save_frontend_code]

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
        llm = create_litellm(token, model="gemini-2.5-pro-litellm-usw1")
        proj = get_or_create_project(project_id, req_session_id)

        artifacts_section = [
            "",
            "## Technical artifacts",
            proj.technical_artifacts_md or "(not available)",
        ]

        # First turn: backend
        backend_prompt = "\n".join([f"project_id={project_id}"] + artifacts_section)
        try:
            await run_turn(
                AGENT_FACTORIES["codegen_backend"](llm, tools=self._backend_codegen_tools()),
                session_id=f"{req_session_id}-codegen-backend",
                message=backend_prompt,
            )
        except Exception as e:
            # Tool may have executed even if final confirmation POST was blocked (e.g. WAF)
            logger.warning("Backend codegen run_turn error (may be harmless if save_backend_code was called): %s", e)

        # Second turn: frontend
        frontend_prompt = "\n".join([f"project_id={project_id}"] + artifacts_section)
        try:
            await run_turn(
                AGENT_FACTORIES["codegen_frontend"](llm, tools=self._frontend_codegen_tools()),
                session_id=f"{req_session_id}-codegen-frontend",
                message=frontend_prompt,
            )
        except Exception as e:
            logger.warning("Frontend codegen run_turn error (may be harmless if save_frontend_code was called): %s", e)

        proj = get_or_create_project(project_id, req_session_id)

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
