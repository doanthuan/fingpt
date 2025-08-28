from typing import Any

from app.assistant_v2.card.graph.node import call_model_func
from app.assistant_v2.card.state import CardAgentState
from app.assistant_v2.primary.card_controller import CardController
from app.prompt.prompt_module import PromptModule
from promptfoo.common.common_agent_runner import common_call_api, generic_agent_router

module = PromptModule()


async def call_api(
    prompt: str,
    options: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    return await common_call_api(
        prompt, options, context, CardAgentState, call_model_func
    )


async def card_agent_router(
    prompt: str,
    options: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    return await generic_agent_router(
        prompt, options, context, CardController.build_agent
    )
