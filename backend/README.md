# ProtoPilot Backend

## Environment Variables

Set in `backend/.env`:

| Variable | Description |
|---|---|
| `CLIENT_ID` / `CLIENT_SECRET` | OAuth credentials |
| `LITELLM_API_KEY` / `LITELLM_MODEL` / `LITELLM_API_BASE` | LLM proxy config |
| `LITELLM_MODEL_ARTIFACT`, `LITELLM_MODEL_CODEGEN` | Per-agent model override (optional) |

## Run

```bash
uvicorn api.server:app --reload --port 8000
```

## Stage Flow

```
REQ → ARTIFACTS_NON_TECH → WAIT_APPROVAL → TECH_ARTIFACTS → CODEGEN → QA
```

| Stage | Trigger | Agent | Key tool call |
|---|---|---|---|
| REQ | User message | Requirements Agent | `submit_spec` |
| ARTIFACTS_NON_TECH | Auto after REQ | Artifacts Agent (non_tech) | `save_nontech_artifacts` |
| WAIT_APPROVAL | — | No model call | `approve` / `change` |
| TECH_ARTIFACTS | User approves | Artifacts Agent (technical) | `save_technical_artifacts` |
| CODEGEN | Auto after TECH | Code Generation Agent | `save_generated_code` |
| QA | Auto after CODEGEN | — | — |

CODEGEN injects `api_documentation.md` into the prompt and renders output via StackBlitz.

## Troubleshooting

- **Stage stuck**: check logs for missing tool call; if absent, model hit token limit.
- **CODEGEN empty**: confirm `api_documentation.md` was saved in TECH_ARTIFACTS stage.
