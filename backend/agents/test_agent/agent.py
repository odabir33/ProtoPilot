import base64
import os

import httpx
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()


# Step 1: Get OAuth Token
async def get_oauth_token(client_id: str, client_secret: str) -> str:
    """Get OAuth token using client credentials."""
    token_url = "https://api-uat.cotality.com/oauth/token?grant_type=client_credentials"
    
    auth_string = f"{client_id}:{client_secret}"
    encoded_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data={"grant_type": "client_credentials"},
            headers=headers,
        )
        response.raise_for_status()
        return response.json()["access_token"]


# Step 2: Create LiteLLM Object
def create_litellm(oauth_token: str) -> LiteLlm:
    """Create a LiteLLM instance with OAuth token."""

    LITELLM_API_KEY = os.getenv("LITELLM_API_KEY")

    return LiteLlm(
        model=os.getenv("LITELLM_MODEL"),
        api_base=os.getenv("LITELLM_API_BASE"),
        api_key=os.getenv("LITELLM_API_KEY"),
        extra_headers={
            "Authorization": f"Bearer {oauth_token}",
            "x-litellm-api-key": LITELLM_API_KEY,
        },
    )


# Step 3: Create LLM Agent
def create_agent(llm: LiteLlm) -> LlmAgent:
    """Create an ADK agent with LiteLLM."""
    instructions = "You are a helpful AI assistant."
    
    return LlmAgent(
        model=llm,
        name="myAgent",
        description="Agent powered by LiteLLM",
        instruction=instructions,
        generate_content_config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=4096,
        ),
    )


# Usage
async def main():

    USER_ID = os.getenv("USER_ID")
    APP_NAME = os.getenv("APP_NAME")
    SESSION_ID = os.getenv("SESSION_ID")

    # Get OAuth token
    token = await get_oauth_token(
        os.getenv("CLIENT_ID"),
        os.getenv("CLIENT_SECRET")
    )
    print("Got OAuth token", token)
    
    # Create LiteLLM object with token
    llm = create_litellm(token)
    print("Created LiteLLM object with OAuth token")
    
    # Create session
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    print("Session created: ", session.id)

    # Create agent and runner
    agent = create_agent(llm)
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    print("Created agent and runner")
    
    # Run agent
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=types.Content(
            role="user", parts=[types.Part("What is Python?")]
        ),
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())