from typing import Any, Dict

from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import (
    PENDING_RESPONSE_KEY,
    PROMPT_SERVICE_KEY,
    THREAD_ID_KEY,
)
from app.assistant_v2.term_deposit.graph.tool import tool_list, tool_names
from app.assistant_v2.term_deposit.graph.utils import (
    chain_ainvoke,
    extract_tool_messages,
)
from app.assistant_v2.term_deposit.state import (
    TermDepositAgentState,
    TermDepositAgentStateFields,
)
from app.assistant_v2.util.handle_ai_message import verify_ai_message
from app.assistant_v2.util.misc import build_chain, extract_config
from app.core.config import settings
from app.entity import ChatRespAction, ChatRespDto
from app.prompt.prompt_service import PromptService
from app.utils.modified_langfuse_decorator import observe

call_model_node = NodeName("call_model")


@observe()
async def call_model_func(
    state: TermDepositAgentState,
    config: RunnableConfig,
    prompt_name: str = settings.term_deposit_v2_extract_info_prompt,
    prompt_label: str = settings.term_deposit_v2_extract_info_label,
) -> Dict[str, Any]:
    messages = state[TermDepositAgentStateFields.MESSAGES]
    config_data, ctx, logger = extract_config(config)
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
    retry_counter = 0
    while True:
        response: Any = await chain_ainvoke(chain, {"messages": messages})
        new_message = verify_ai_message(
            ctx, state, response, retry_counter, expected_tools=tool_names
        )
        if new_message:
            messages = new_message
            retry_counter += 1
        else:
            break
    output[TermDepositAgentStateFields.MESSAGES] = [response]
    if not response.tool_calls:
        chat_response = ChatRespDto(
            action=ChatRespAction.SHOW_REPLY,
            thread_id=config_data[THREAD_ID_KEY],
            response=response.content,
            metadata=None,
        )
        config_data[PENDING_RESPONSE_KEY].append(chat_response)
    return output
