import os
import litellm
from google.adk.models.lite_llm import LiteLlm

# Prevent LiteLLM from trying to serialize httpx internals (httpx.URL bug)
litellm.suppress_debug_info = True


def create_litellm(oauth_token: str, model: str | None = None) -> LiteLlm:
    litellm_api_key = os.getenv("LITELLM_API_KEY", "")
    default_model = os.getenv("LITELLM_MODEL", "")
    api_base = os.getenv("LITELLM_API_BASE", "")

    if not (litellm_api_key and default_model and api_base):
        raise RuntimeError("Missing LITELLM_API_KEY / LITELLM_MODEL / LITELLM_API_BASE in .env")

    resolved_model = model if model else default_model

    return LiteLlm(
        model=resolved_model,
        api_base=api_base,
        api_key=litellm_api_key,
        custom_llm_provider="openai",
        extra_headers={
            "Authorization": f"Bearer {oauth_token}",
            "x-litellm-api-key": litellm_api_key,
        },
    )
