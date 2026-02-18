from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .instructions import REQUIREMENTS_GATHERING_AGENT_INSTRUCTIONS
import os

try:
    from dotenv import load_dotenv
    load_dotenv()

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
except ImportError:
    print("Warning: python-dotenv not installed. Ensure API key is set")

custom_model = LiteLlm(
    model="groq/llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY
)


root_agent = Agent(
    model=custom_model,
    name="reqs_gathering_agent",
    description="A Technical Product Manager Assistant",
    instruction=REQUIREMENTS_GATHERING_AGENT_INSTRUCTIONS,
)

