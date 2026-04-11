from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from orchestration.orchestrator import Orchestrator
from orchestration.store import get_job
from core.parse_spec import extract_questions

router = APIRouter()
orch = Orchestrator()

class ChatRequest(BaseModel):
    project_id: str
    session_id: str
    message: str

@router.post("/chat")
async def chat(req: ChatRequest):
    try:
        result = await orch.handle(req.project_id, req.session_id, req.message)

        questions = []
        if result.get("stage") == "REQ":
            questions = extract_questions(result.get("reply", ""))

        return {
            "project_id": req.project_id,
            "session_id": req.session_id,
            **result,
            "questions": questions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def job_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
