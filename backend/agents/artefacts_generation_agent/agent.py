from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .instructions import ARTEFACTS_GENERATION_AGENT_INSTRUCTIONS
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
except ImportError:
    print("Warning: python-dotenv not installed. Ensure API key is set")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

custom_model = LiteLlm(
    model="groq/llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY
)

root_agent = Agent(
    model=custom_model,
    name="artefacts_generation_agent",
    description="Generates project artefacts from structured requirements JSON",
    instruction=ARTEFACTS_GENERATION_AGENT_INSTRUCTIONS,
)
