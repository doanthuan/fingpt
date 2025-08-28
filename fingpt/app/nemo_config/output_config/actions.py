import logging
from typing import Optional

from langchain.llms.base import BaseLLM  # type: ignore
from nemoguardrails import RailsConfig  # type: ignore
from nemoguardrails.actions.actions import action  # type: ignore
from nemoguardrails.actions.llm.utils import llm_call  # type: ignore
from nemoguardrails.llm.params import llm_params  # type: ignore
from nemoguardrails.llm.taskmanager import LLMTaskManager  # type: ignore

log = logging.getLogger(__name__)


@action(is_system_action=True)
async def self_check_bot_response(
    llm_task_manager: LLMTaskManager,
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None,
    config: Optional[RailsConfig] = None,
):
    bot_response = context.get("user_message")  # type: ignore

    if bot_response:
        prompt = llm_task_manager.render_task_prompt(
            task="self_check_bot_response",
            context={
                "bot_response": bot_response,
            },
        )

    with llm_params(llm, model_kwargs={"temperature": config.lowest_temperature}):  # type: ignore
        response = await llm_call(llm, prompt)

        log.info(f"Json format response is:\n{response}.")

    return response
