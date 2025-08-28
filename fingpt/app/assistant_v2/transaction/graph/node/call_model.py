import json
from typing import Any, Dict, List

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import (
    PENDING_RESPONSE_KEY,
    PROMPT_SERVICE_KEY,
    THREAD_ID_KEY,
)
from app.assistant_v2.transaction.constant import FILTER_TRANSACTION_TOOL_NAME
from app.assistant_v2.transaction.graph.tool import tool_list
from app.assistant_v2.transaction.state import (
    TransactionAgentState,
    TransactionAgentStateFields,
)
from app.assistant_v2.util.handle_ai_message import verify_ai_message
from app.assistant_v2.util.misc import build_chain, extract_config
from app.core.config import settings
from app.entity import ChatRespAction, ChatRespDto, Transaction
from app.prompt.prompt_service import PromptService
from app.utils.modified_langfuse_decorator import observe

call_model_node = NodeName("call_model")


def _parse_processed_transactions(content: str) -> Dict[str, List[Transaction]]:
    from_json = json.loads(content)
    return {
        key: [Transaction(**value) for value in values]
        for key, values in from_json.items()
    }


def extract_tool_messages(logger, messages) -> Dict[str, Any]:
    logger.info("Extracting tool messages...")
    output = {}
    for message in messages[::-1]:
        if not isinstance(message, ToolMessage):
            break
        logger.debug(f"Tool message: {message}")
        if message.name == FILTER_TRANSACTION_TOOL_NAME:
            output[TransactionAgentStateFields.PROCESSED_TRANSACTIONS] = (
                _parse_processed_transactions(message.content)
            )
    if (
        TransactionAgentStateFields.PROCESSED_TRANSACTIONS in output
        and len(output[TransactionAgentStateFields.PROCESSED_TRANSACTIONS]) == 1
    ):
        output[TransactionAgentStateFields.CONFIRMED_TRANSACTIONS] = list(
            output[TransactionAgentStateFields.PROCESSED_TRANSACTIONS].values()
        )[0]

    return output


async def _chain_ainvoke(chain, input_data: Dict[str, Any]) -> AIMessage:
    return await chain.ainvoke(input_data)


@observe()
async def call_model_func(
    state: TransactionAgentState,
    config: RunnableConfig,
    prompt_name: str = settings.transaction_report_search_term_prompt,
    prompt_label: str = settings.transaction_report_search_term_label,
) -> Dict[str, Any]:
    messages = state[TransactionAgentStateFields.MESSAGES]
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
        response = await _chain_ainvoke(chain, {"messages": messages})
        new_message = verify_ai_message(ctx, state, response, retry_counter)
        if new_message:
            messages = new_message
            retry_counter += 1
        else:
            break

    output[TransactionAgentStateFields.MESSAGES] = [response]
    if not response.tool_calls:
        chat_response = ChatRespDto(
            action=ChatRespAction.SHOW_REPLY,
            thread_id=config_data[THREAD_ID_KEY],
            response=response.content,
            metadata=None,
        )
        config_data[PENDING_RESPONSE_KEY].append(chat_response)
    return output
