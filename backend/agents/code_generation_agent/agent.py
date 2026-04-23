import os
from google.genai import types
from google.adk.agents import LlmAgent
from core.llm import create_litellm
from .instructions import CODE_GENERATION_AGENT_INSTRUCTIONS

def create_agent(token: str, tools=None) -> LlmAgent:
    llm = create_litellm(token, model=os.getenv("LITELLM_MODEL_CODEGEN"))
    return LlmAgent(
        model=llm,
        name="codegen_frontend_agent",
        description="Generate production-ready Angular frontend code from specifications",
        instruction=CODE_GENERATION_AGENT_INSTRUCTIONS,
        tools=tools or [],
        generate_content_config=types.GenerateContentConfig(
            temperature=0.2,          
            max_output_tokens=65535,
        ),
    )
