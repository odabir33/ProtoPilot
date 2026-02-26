from typing import Awaitable, Callable

ChatFn = Callable[[str, str], Awaitable[str]]  # (session_id, message) -> reply

from agents.requirements_gathering_agent.run import chat as requirements_chat

AGENT_CHAT: dict[str, ChatFn] = {
    "requirements": requirements_chat,
}