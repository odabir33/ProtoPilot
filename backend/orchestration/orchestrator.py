from agents.registry import AGENT_CHAT

class Orchestrator:
    async def chat(self, agent: str, session_id: str, message: str) -> str:
        if agent not in AGENT_CHAT:
            raise ValueError(f"Unknown agent: {agent}")
        return await AGENT_CHAT[agent](session_id, message)