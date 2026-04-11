from typing import Callable, Any
from agents.requirements_gathering_agent.agent import create_agent as create_req_agent
from agents.artefacts_generation_agent.agent import create_agent as create_art_agent
from agents.codegen_agent.agent import create_backend_agent, create_frontend_agent

AgentFactory = Callable[..., Any]  # llm + optional kwargs -> LlmAgent

AGENT_FACTORIES: dict[str, AgentFactory] = {
    "requirements": create_req_agent,
    "artifacts": create_art_agent,
    "codegen_backend": create_backend_agent,
    "codegen_frontend": create_frontend_agent,
}
