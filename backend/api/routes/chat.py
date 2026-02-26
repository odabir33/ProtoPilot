from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from orchestration.orchestrator import Orchestrator
from core.parse_spec import extract_json_block, infer_done

router = APIRouter()
orch = Orchestrator()

class ChatRequest(BaseModel):
    agent: str 
    session_id: str
    message: str

@router.post("/chat")
async def chat(req: ChatRequest):
    try:
        reply = await orch.chat(req.agent, req.session_id, req.message)

        spec = extract_json_block(reply)
        done = infer_done(reply, spec)

        return {
            "session_id": req.session_id,
            "reply": reply,
            "done": done,
            "spec": spec,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))