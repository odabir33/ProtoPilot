# ProtoPilot Backend

FastAPI backend for a stage-driven multi-agent workflow built with Google ADK.
Generates a full-stack Spring Boot + Angular application from a natural language description and runs it locally.


## 1. Project Structure

```text
backend/
├── api/
│   ├── server.py                      # FastAPI app entry
│   └── routes/chat.py                 # /chat and /jobs endpoints
├── orchestration/
│   ├── orchestrator.py                # Stage controller
│   ├── store.py                       # In-memory project state
│   ├── tools.py                       # Function-calling tools
│   └── local_deploy.py                # Local Spring Boot + Angular deploy
├── agents/
│   ├── requirements_gathering_agent/
│   │   ├── agent.py
│   │   └── instructions.py
│   ├── artefacts_generation_agent/
│   │   ├── agent.py
│   │   └── instructions.py
│   ├── codegen_agent/
│   │   ├── agent.py                   # Backend + frontend agent factories
│   │   └── instructions.py            # Split backend/frontend instructions
│   └── registry.py                    # Agent factory registry
├── core/
│   ├── auth.py                        # OAuth token
│   ├── llm.py                         # LiteLLM wrapper
│   ├── runner.py                      # ADK runner bridge (SSE streaming)
│   └── parse_spec.py                  # Question extraction
└── requirements.txt
```


## 2. System Dependencies

Install before running:

```bash
brew install openjdk@17 maven
echo 'export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"' >> ~/.zshrc
echo 'export JAVA_HOME="/opt/homebrew/opt/openjdk@17"' >> ~/.zshrc
source ~/.zshrc
npm install -g @angular/cli@17
```


## 3. Environment Variables

Set in `backend/.env`:

```
CLIENT_ID=
CLIENT_SECRET=
LITELLM_API_KEY=
LITELLM_MODEL=
LITELLM_API_BASE=
USER_ID=local-user      # optional
APP_NAME=ProtoPilot     # optional
```


## 4. Run

```bash
cd backend
pip install -r requirements.txt
uvicorn api.server:app --reload --port 8000
```

Health check: `GET /health`


## 5. Pipeline

```
REQ → ARTIFACTS_NON_TECH → WAIT_APPROVAL → TECH_ARTIFACTS → CODEGEN → DEPLOY → QA
```

| Stage | Trigger | Model | Description |
|---|---|---|---|
| `REQ` | User message | Gemini 2.5 Flash | Multi-turn requirements gathering, finalized via `submit_spec` |
| `ARTIFACTS_NON_TECH` | Automatic | Gemini 2.5 Flash | Generates PRD, user stories, and other PM documents |
| `WAIT_APPROVAL` | User message | None | `approve` to continue, `change` to revise requirements |
| `TECH_ARTIFACTS` | Automatic | Gemini 2.5 Pro | Generates system design, API docs, database schema |
| `CODEGEN` | Automatic (background job) | Gemini 2.5 Pro | Two LLM calls: backend first, then frontend |
| `DEPLOY` | Automatic (background job) | None | Writes files locally, starts Spring Boot + Angular |
| `QA` | Automatic | — | Deploy complete, `preview_url` available |


## 6. Chat API

### POST /chat

```json
{
  "project_id": "p1",
  "session_id": "s1",
  "message": "Build a team task app"
}
```

### Response Fields

| Field | Description |
|-------|-------------|
| `stage` | Current pipeline stage |
| `reply` | Status message |
| `job_id` | Async job ID (present during CODEGEN/DEPLOY stages) |
| `spec` | Requirements JSON |
| `nontech_artifacts_md` | PM-facing markdown artifacts |
| `technical_artifacts_md` | Technical markdown artifacts |
| `preview_url` | Preview URL once deployed (`http://localhost:4200`) |
| `questions` | Clarification questions (REQ stage only) |

### GET /jobs/{job_id}

轮询异步 job 状态：

```json
{ "status": "running|done|failed", "result": {}, "error": null }
```

**Polling flow:**
1. Receive `CODEGEN_PENDING` → poll codegen job
2. Codegen done, get `job_id` from result → poll deploy job
3. Deploy done, get `preview_url` from result → render iframe


## 7. Tools (Function Calling)

| Tool | Stage | Description |
|------|-------|-------------|
| `submit_spec` | REQ | Saves requirements, advances to ARTIFACTS_NON_TECH |
| `load_spec` | ARTIFACTS | Loads requirements spec |
| `save_nontech_artifacts` | ARTIFACTS_NON_TECH | Saves PM docs, advances to WAIT_APPROVAL |
| `save_technical_artifacts` | TECH_ARTIFACTS | Saves technical docs, advances to CODEGEN |
| `save_backend_code` | CODEGEN | Saves Spring Boot files to memory |
| `save_frontend_code` | CODEGEN | Saves Angular files to memory, advances to DEPLOY |
| `set_project_stage` | Any | Force-sets pipeline stage |

Tool call log format: `[TOOL_CALL] <tool_name> {...}`


## 8. Notes

- All state is in-memory (`orchestration/store.py`) — restarting the server clears all project state
- `project_id` identifies project state; `session_id` is the ADK conversation context
- Generated code is written to `/tmp/protopilot_deploy/`; logs at `backend.log` / `frontend.log`
- SSE streaming is enabled on all LLM calls to avoid LiteLLM proxy gateway timeouts
