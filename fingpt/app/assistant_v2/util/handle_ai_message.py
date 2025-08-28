import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import add_messages

from app.assistant_v2.common.base_agent_state import BaseAgentStateFields
from app.core import RequestContext


def _has_content(message: BaseMessage) -> bool:
    if not message.content or message.content == "":
        return False
    return True


def _verify_content(message: BaseMessage) -> bool:

    # No verification needed if content is empty
    if not _has_content(message):
        return True

    # @SONAR_STOP@
    pattern = r"\[.*?functions\..*\]|\[*?Call.*\]"
    # @SONAR_START@
    match = re.search(pattern, message.content)
    if match:
        return False

    return True


def verify_ai_message(
    ctx: RequestContext,
    state: Dict[str, Any],
    ai_result,
    retry_counter,
    maximum_retries=3,
    minimum_tool_calls=0,
    maximum_tool_calls=float("inf"),
    expected_tools=None,
) -> Optional[List[BaseMessage]]:
    """
    Handle missing tool calls in the AI result.

    Args:
        ctx: RequestContext
        state: Dict[str, Any]: The state of the agent
        ai_result: The AI result
        retry_counter: The number of retries
        maximum_retries: The maximum number of retries
        minimum_tool_calls: The minimum number of tool calls expected in the AI result
        maximum_tool_calls: The maximum number of tool calls expected in the AI result
        expected_tools: The list of expected tool calls

    Returns:
        True: If the missing tool call is handled successfully
        False: If the missing tool call is not handled successfully or retry counter is exceeded
    """

    logger = ctx.logger()
    if retry_counter > maximum_retries:
        logger.error("Exceeded maximum retries for missing tool calls")
        return None

    if not _verify_content(ai_result):
        logger.debug(
            f"Invalid content found in the AI result: {ai_result}. Retrying..."
        )
        messages = add_messages(
            state[BaseAgentStateFields.MESSAGES],
            [
                SystemMessage("Content must not contain any function calls."),
            ],
        )
        logger.info("Retrying with instruction message")
        return messages

    tool_calls_name = (
        [tool_call.get("name") for tool_call in ai_result.tool_calls]
        if ai_result.tool_calls
        else []
    )
    invalid_tool_calls = (
        [tool_name for tool_name in tool_calls_name if tool_name not in expected_tools]
        if expected_tools
        else []
    )
    if invalid_tool_calls:
        logger.debug(f"Tool calls {invalid_tool_calls} are not valid. Retrying...")
        messages = add_messages(
            state[BaseAgentStateFields.MESSAGES],
            [
                SystemMessage(
                    f"Your provided tools are: {expected_tools}. DO NOT MAKE UP NEW TOOLS!"
                ),
            ],
        )
        logger.info("Retrying with the updated messages to get valid output...")
        return messages

    num_tool_calls = len(tool_calls_name)
    if num_tool_calls == 0 and not _has_content(ai_result):
        logger.debug(
            f"Tool call or content is expected but not found in the AI result: {ai_result}. Retrying..."
        )
        messages = add_messages(
            state[BaseAgentStateFields.MESSAGES],
            [
                SystemMessage("Response must contain a tool calls or content."),
            ],
        )
        logger.info("Retrying with the updated messages to get valid output...")
        return messages

    elif num_tool_calls < minimum_tool_calls:
        logger.debug(
            f"{minimum_tool_calls} Tool calls is expected but not found in the AI result: {ai_result}. Retrying..."
        )
        messages = add_messages(
            state[BaseAgentStateFields.MESSAGES],
            [
                SystemMessage("Only response with tool call."),
            ],
        )
        logger.info("Retrying with the updated messages to get valid output...")
        return messages
    elif num_tool_calls > maximum_tool_calls:
        logger.debug(
            f"Only one tool call is expected but found {num_tool_calls} in the AI result: "
            f"{ai_result}. Retrying..."
        )
        messages = add_messages(
            state[BaseAgentStateFields.MESSAGES],
            [
                SystemMessage(
                    f"Only response with at most {maximum_tool_calls} tool calls."
                ),
            ],
        )
        logger.info("Retrying with the updated messages to get valid output...")
        return messages
    return None
