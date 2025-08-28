from typing import Any, Dict

from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.card.graph.tool import tool_list
from app.assistant_v2.card.graph.utils import chain_ainvoke, extract_tool_messages
from app.assistant_v2.card.state import CardAgentState, CardAgentStateFields
from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    PENDING_RESPONSE_KEY,
    PROMPT_SERVICE_KEY,
    THREAD_ID_KEY,
)
from app.assistant_v2.util.misc import build_chain
from app.core import RequestContext
from app.core.config import settings
from app.entity import ChatRespAction, ChatRespDto
from app.prompt.prompt_service import PromptService
from app.utils.modified_langfuse_decorator import observe

call_model_node = NodeName("call_model")


@observe()
async def call_model_func(
    state: CardAgentState,
    config: RunnableConfig,
    prompt_name: str = settings.card_v2_extract_user_query_prompt,
    prompt_label: str = settings.card_v2_extract_user_query_label,
) -> Dict[str, Any]:
    messages = state[CardAgentStateFields.MESSAGES]
    config_data = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()
    output = extract_tool_messages(logger, messages)

    logger.info("Calling llm...")
    ps: PromptService = config_data[PROMPT_SERVICE_KEY]
    chain = await build_chain(
        ctx,
        ps,
        prompt_name,
        prompt_label,
        tool_list,
    )
    response = await chain_ainvoke(chain, {"messages": messages})
    output[CardAgentStateFields.MESSAGES] = [response]
    if not response.tool_calls:
        chat_response = ChatRespDto(
            action=ChatRespAction.SHOW_REPLY,
            thread_id=config_data[THREAD_ID_KEY],
            response=response.content,
            metadata=None,
        )
        config_data[PENDING_RESPONSE_KEY].append(chat_response)
    return output
