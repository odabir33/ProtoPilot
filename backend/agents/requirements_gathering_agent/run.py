from core.auth import get_oauth_token
from core.llm import create_litellm
from core.runner import run_turn

from agents.requirements_gathering_agent.agent import create_agent

async def chat(session_id: str, message: str) -> str:
    token = await get_oauth_token()
    llm = create_litellm(token)
    agent = create_agent(llm)
    return await run_turn(agent, session_id=session_id, message=message)