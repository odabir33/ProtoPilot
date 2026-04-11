from google.adk.agents import LlmAgent
from google.genai import types

from .instructions import CODEGEN_BACKEND_INSTRUCTIONS, CODEGEN_FRONTEND_INSTRUCTIONS


def create_backend_agent(llm, tools=None) -> LlmAgent:
    return LlmAgent(
        model=llm,
        name="codegen_backend_agent",
        description="Generates Spring Boot backend source files into a dict",
        instruction=CODEGEN_BACKEND_INSTRUCTIONS,
        tools=tools or [],
        generate_content_config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=65535,
        ),
    )


def create_frontend_agent(llm, tools=None) -> LlmAgent:
    return LlmAgent(
        model=llm,
        name="codegen_frontend_agent",
        description="Generates Angular frontend source files into a dict",
        instruction=CODEGEN_FRONTEND_INSTRUCTIONS,
        tools=tools or [],
        generate_content_config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=65535,
        ),
    )
