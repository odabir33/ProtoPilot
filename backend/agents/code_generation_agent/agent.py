from google.genai import types
from google.adk.agents import LlmAgent
from .instructions import CODE_GENERATION_AGENT_INSTRUCTIONS

def create_agent(llm, tools=None) -> LlmAgent:
    return LlmAgent(
        model=llm,
        name="code_generation_agent",
        description="Generate production-ready Angular frontend code from specifications",
        instruction=CODE_GENERATION_AGENT_INSTRUCTIONS,
        tools=tools or [],
        generate_content_config=types.GenerateContentConfig(
            temperature=0.3,          
            max_output_tokens=16384,
        ),
    )
