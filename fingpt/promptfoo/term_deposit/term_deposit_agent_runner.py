from typing import Any

from app.assistant_v2.primary.term_deposit_controller import TermDepositController
from app.assistant_v2.term_deposit.graph.node import call_model_func
from app.assistant_v2.term_deposit.state import TermDepositAgentState
from app.prompt.prompt_module import PromptModule
from promptfoo.common.common_agent_runner import common_call_api, generic_agent_router

module = PromptModule()


async def call_api(
    prompt: str,
    options: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    return await common_call_api(
        prompt, options, context, TermDepositAgentState, call_model_func
    )


async def term_deposit_agent_router(
    prompt: str,
    options: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    return await generic_agent_router(
        prompt, options, context, TermDepositController.build_agent
    )
