# ProtoPilot Backend

FastAPI backend for a stage-driven multi-agent workflow built with Google ADK.


## 1. Project Structure

```text
backend/
├── api/
│   ├── server.py              # FastAPI app entry
│   └── routes/chat.py         # /chat endpoint
├── orchestration/
│   ├── orchestrator.py        # Stage controller
│   ├── store.py               # In-memory project state
│   └── tools.py               # Function-calling tools
├── agents/
│   ├── requirements_gathering_agent/
│   │   ├── agent.py
│   │   └── instructions.py
│   ├── artefacts_generation_agent/
│   │   ├── agent.py
│   │   └── instructions.py
│   └── registry.py            # Agent factory registry
├── core/
│   ├── auth.py                # OAuth token
│   ├── llm.py                 # LiteLLM wrapper
│   ├── runner.py              # ADK runner bridge
│   └── parse_spec.py          # Question extraction
└── requirements.txt
```


## 2. Environment Variables

Set in `backend/.env`:

- `CLIENT_ID`
- `CLIENT_SECRET`
- `LITELLM_API_KEY`
- `LITELLM_MODEL`
- `LITELLM_API_BASE`
- `USER_ID` (optional, default: `local-user`)
- `APP_NAME` (optional, default: `ProtoPilot`)

## 3. Run

```bash
uvicorn api.server:app --reload --port 8000
```

Health checks:

- `GET /`
- `GET /health`

## 4. Chat API

### Request

`POST /chat`

```json
{
  "project_id": "p1",
  "session_id": "s1",
  "message": "Build a team task app"
}
```

### Response Fields

- `project_id`: request project id
- `session_id`: request session id
- `stage`: current stage enum
- `reply`: short stage/status message
- `spec`: latest requirements JSON (if available)
- `nontech_artifacts_md`: non-technical markdown artifacts
- `technical_artifacts_md`: technical markdown artifacts
- `artifacts_md`: convenience field (current/last artifact markdown)
- `questions`: extracted clarification questions (only when stage is `REQ`)

## 5. Stage Flow

### REQ

- Runs Requirements Agent.
- Agent uses tool call `submit_spec(project_id, spec)` to finalize.
- On success, stage moves to `ARTIFACTS_NON_TECH`.

### ARTIFACTS_NON_TECH

- Runs Artifacts Agent in `phase=non_tech`.
- Agent should call:
  1. `load_spec(project_id)`
  2. `save_nontech_artifacts(project_id, artifacts_md)`
- On success, stage moves to `WAIT_APPROVAL`.

### WAIT_APPROVAL

- No model call.
- User message handling:
  - `approve` -> `TECH_ARTIFACTS`
  - `change` -> `REQ` (revision mode)

### TECH_ARTIFACTS

- Runs Artifacts Agent in `phase=technical`.
- Agent should call:
  1. `load_spec(project_id)`
  2. `save_technical_artifacts(project_id, artifacts_md)`
- On success, stage moves to `CODEGEN`.

### CODEGEN / QA

- Placeholder stages for downstream pipelines.

## 6. Tools (Function Calling)

Defined in `orchestration/tools.py`:

- `submit_spec(project_id, spec)`
- `load_spec(project_id)`
- `save_nontech_artifacts(project_id, artifacts_md)`
- `save_technical_artifacts(project_id, artifacts_md)`
- `set_project_stage(project_id, stage)`

Tool calls are logged as:

```text
[TOOL_CALL] <tool_name> {...}
```

## 7. Important Behavior Notes

- State store is in-memory only (`orchestration/store.py`).
  - Restarting server clears all project/session state.
- `project_id` identifies project state.
- `session_id` is conversation context id used by ADK runner.
- `reply` is intentionally short for artifact stages.
  - Full artifact content should be read from `nontech_artifacts_md` or `technical_artifacts_md`.

## 8. Troubleshooting

### Stage stuck at `ARTIFACTS_NON_TECH` or `TECH_ARTIFACTS`

Check logs for missing save tool call:

- `save_nontech_artifacts`
- `save_technical_artifacts`

If missing, inspect token limits.

### Token cutoff / incomplete generation

- Increase agent `max_output_tokens` in agent config.
- Keep `reply` short and persist full markdown via save tools.


