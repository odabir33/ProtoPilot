from google.adk.agents import LlmAgent
from google.genai import types
from .instructions import REQUIREMENTS_GATHERING_AGENT_INSTRUCTIONS

def create_agent(llm, tools=None) -> LlmAgent:
    return LlmAgent(
        model=llm,
        name="reqs_gathering_agent",
        description="A Technical Product Manager Assistant",
        instruction=REQUIREMENTS_GATHERING_AGENT_INSTRUCTIONS,
        tools=tools or [],
        generate_content_config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=4096,
        ),
    )
