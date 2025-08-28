from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolCall

from app.assistant_v2.common.base_agent_state import BaseAgentStateFields
from app.assistant_v2.util.handle_ai_message import (
    _has_content,
    _verify_content,
    verify_ai_message,
)


@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.logger.return_value = MagicMock()
    return ctx


@pytest.fixture
def mock_state():
    return {BaseAgentStateFields.MESSAGES: [HumanMessage(content="test message")]}


def test_verify_ai_message_no_tool_calls_invalid_content(mock_context, mock_state):
    ai_result = AIMessage(content="")
    ai_result.tool_calls = None
    retry_counter = 0

    result = verify_ai_message(mock_context, mock_state, ai_result, retry_counter)
    assert result is not None
    assert len(result) == 2
    assert isinstance(result[-1], SystemMessage)
    assert result[-1].content == "Response must contain a tool calls or content."


def test_verify_ai_message_less_than_minimum_tool_calls(mock_context, mock_state):
    ai_result = AIMessage(content="Valid content")
    ai_result.tool_calls = []
    retry_counter = 0

    result = verify_ai_message(
        mock_context, mock_state, ai_result, retry_counter, minimum_tool_calls=1
    )
    assert result is not None
    assert len(result) == 2
    assert isinstance(result[-1], SystemMessage)
    assert result[-1].content == "Only response with tool call."


def test_verify_ai_message_more_than_maximum_tool_calls(mock_context, mock_state):
    ai_result = AIMessage(
        content="Valid content",
        tool_calls=[
            ToolCall(name="tool1", id="123", args={}),
            ToolCall(name="tool2", id="456", args={}),
        ],
    )
    retry_counter = 0

    result = verify_ai_message(
        mock_context, mock_state, ai_result, retry_counter, maximum_tool_calls=1
    )
    assert result is not None
    assert len(result) == 2
    assert isinstance(result[-1], SystemMessage)
    assert result[-1].content == "Only response with at most 1 tool calls."


def test_verify_ai_message_valid_tool_calls_and_content(mock_context, mock_state):
    ai_result = AIMessage(
        content="Valid content",
        tool_calls=[ToolCall(name="tool1", id="123", args={})],
    )
    retry_counter = 0

    result = verify_ai_message(mock_context, mock_state, ai_result, retry_counter)
    assert result is None


def test_verify_ai_message_exceed_maximum_retries(mock_context, mock_state):
    ai_result = AIMessage(content="")
    ai_result.tool_calls = None
    retry_counter = 4

    result = verify_ai_message(
        mock_context, mock_state, ai_result, retry_counter, maximum_retries=3
    )
    assert result is None


def test_verify_ai_message_invalid_tool(mock_context, mock_state):
    ai_result = AIMessage(
        content="",
        tool_calls=[
            ToolCall(name="invalid_tool", id="123", args={}),
            ToolCall(name="invalid_tool2", id="456", args={}),
            ToolCall(name="valid_tool1", id="789", args={}),
        ],
    )
    result = verify_ai_message(
        mock_context,
        mock_state,
        ai_result,
        0,
        expected_tools=["valid_tool1", "valid_tool2"],
    )
    assert result is not None
    assert len(result) == 2
    assert isinstance(result[-1], SystemMessage)
    assert (
        result[-1].content
        == "Your provided tools are: ['valid_tool1', 'valid_tool2']. DO NOT MAKE UP NEW TOOLS!"
    )


def test_verify_has_content():
    message = AIMessage(content="Valid content")
    message_2 = AIMessage(content="")
    assert _has_content(message) is True
    assert _has_content(message_2) is False


def test_verify_invalid_content():
    message = AIMessage(
        content="Sure, I can help you with that.\n\n [Assistant to=functions.NoticeDepositAmountTool]"
    )
    message_2 = AIMessage(content="Sure, go to next step")
    mesasge_3 = AIMessage(content="")
    assert _verify_content(message) is False
    assert _verify_content(message_2) is True
    assert _verify_content(mesasge_3) is True
