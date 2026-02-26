import os
from google.adk.models.lite_llm import LiteLlm

def create_litellm(oauth_token: str) -> LiteLlm:
    litellm_api_key = os.getenv("LITELLM_API_KEY", "")
    model = os.getenv("LITELLM_MODEL", "")
    api_base = os.getenv("LITELLM_API_BASE", "")

    if not (litellm_api_key and model and api_base):
        raise RuntimeError("Missing LITELLM_API_KEY / LITELLM_MODEL / LITELLM_API_BASE in .env")

    return LiteLlm(
        model=model,
        api_base=api_base,
        api_key=litellm_api_key,
        extra_headers={
            "Authorization": f"Bearer {oauth_token}",
            "x-litellm-api-key": litellm_api_key,
        },
    )