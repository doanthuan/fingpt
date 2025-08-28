from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    PENDING_RESPONSE_KEY,
    USER_CHOICE_ID_KEY,
)
from app.assistant_v2.primary.card_controller import CardController
from app.assistant_v2.primary.state import AssistantStateFields
from app.entity import ChatRespAction, ChatRespDto


@pytest.fixture
def mock_prompt_service():
    return MagicMock()


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def card_controller(mock_prompt_service, mock_llm):
    return CardController(prompt_srv=mock_prompt_service, llm=mock_llm)


@pytest.fixture
def mock_state():
    return {AssistantStateFields.MESSAGES: ["Test message"]}


@pytest.mark.asyncio
async def test_call_with_pending_response(card_controller, mock_state, agent_config):
    agent_config[CONFIGURABLE_CONTEXT_KEY][PENDING_RESPONSE_KEY] = [
        ChatRespDto(
            action=ChatRespAction.SHOW_REPLY, response="Test response", metadata=None
        )
    ]
    result = await card_controller(mock_state, agent_config)
    assert result == {AssistantStateFields.MESSAGES: []}


@pytest.mark.asyncio
async def test_call_with_user_choice(card_controller, mock_state, agent_config):
    agent_config[CONFIGURABLE_CONTEXT_KEY][USER_CHOICE_ID_KEY] = ["choice_id"]
    result = await card_controller(mock_state, agent_config)
    assert len(result[AssistantStateFields.MESSAGES]) == 1
    assert (
        result[AssistantStateFields.MESSAGES][0].content == "Resume with user choice."
    )


@pytest.mark.asyncio
async def test_call_with_valid_output(card_controller, mock_state, agent_config):
    mock_agent = AsyncMock()
    mock_agent.ainvoke = AsyncMock(return_value=AIMessage(content="New message"))
    card_controller.get_agent = AsyncMock(return_value=mock_agent)

    result = await card_controller(mock_state, agent_config)
    assert result == {AssistantStateFields.MESSAGES: [AIMessage(content="New message")]}


@pytest.mark.asyncio
async def test_call_with_invalid_output(card_controller, mock_state, agent_config):
    mock_agent = AsyncMock()
    mock_agent.ainvoke = AsyncMock(return_value=AIMessage(content="", tool_calls=[]))
    card_controller.get_agent = AsyncMock(return_value=mock_agent)

    with patch(
        "app.assistant_v2.primary.card_controller.verify_ai_message",
        side_effect=[
            [HumanMessage(content="continue")],
            [HumanMessage(content="continue")],
            None,
        ],
    ) as mock_verify:
        await card_controller(mock_state, agent_config)
        assert mock_verify.call_count == 3
