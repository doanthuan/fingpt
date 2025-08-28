from typing import List

from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, CONTEXT_KEY
from app.core import RequestContext
from app.prompt.prompt_service import PromptService


def extract_config(config: RunnableConfig):
    config_data = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()
    return config_data, ctx, logger


@staticmethod
async def build_chain(
    ctx: RequestContext,
    prompt_srv: PromptService,
    prompt_name: str,
    prompt_label: str,
    tool_list: List,
):
    prompt = await prompt_srv.get_prompt(
        ctx,
        name=prompt_name,
        label=prompt_label,
        type="chat",
    )
    prompt_tmpl = prompt.tmpl + MessagesPlaceholder(variable_name="messages")
    prompt_with_tools = prompt_tmpl.partial(
        tool_names=", ".join([tool.name for tool in tool_list])
    )
    agent = prompt_with_tools | prompt.llm_model.bind_tools(tool_list)
    return agent
