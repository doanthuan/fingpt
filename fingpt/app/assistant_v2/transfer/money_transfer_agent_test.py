from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables import Runnable

from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    PENDING_RESPONSE_KEY,
    USER_CHOICE_ID_KEY,
)
from app.assistant_v2.transfer.money_transfer_agent import MoneyTransferAgent
from app.assistant_v2.transfer.state import TransferAgentState, TransferAgentStateFields
from app.core.context import RequestContext


@pytest.mark.asyncio
async def test_call_with_pending_response():
    prompt_srv = MagicMock()
    llm = MagicMock()
    agent = MoneyTransferAgent(prompt_srv, llm)

    state = TransferAgentState(
        {TransferAgentStateFields.MESSAGES: [HumanMessage(content="test message")]}
    )
    config = {
        CONFIGURABLE_CONTEXT_KEY: {
            PENDING_RESPONSE_KEY: ["response"],
            CONTEXT_KEY: MagicMock(RequestContext),
        }
    }

    result = await agent(state, config)

    assert result == {TransferAgentStateFields.MESSAGES: []}


@pytest.mark.asyncio
async def test_call_with_user_choice():
    prompt_srv = MagicMock()
    llm = MagicMock()
    agent = MoneyTransferAgent(prompt_srv, llm)
    context = MagicMock(RequestContext)
    context.request_id.return_value = "123"

    state = TransferAgentState(
        {TransferAgentStateFields.MESSAGES: [HumanMessage(content="test message")]}
    )
    config = {
        CONFIGURABLE_CONTEXT_KEY: {
            USER_CHOICE_ID_KEY: "choice",
            CONTEXT_KEY: context,
        }
    }

    result = await agent(state, config)

    assert len(result[TransferAgentStateFields.MESSAGES]) == 1
    assert isinstance(result[TransferAgentStateFields.MESSAGES][0], AIMessage)
    assert (
        result[TransferAgentStateFields.MESSAGES][0].content
        == "Resume with user choice."
    )


@pytest.mark.asyncio
async def test_call_with_llm_invocation():
    prompt_srv = MagicMock()
    llm = AsyncMock()
    agent = MoneyTransferAgent(prompt_srv, llm)
    context = MagicMock(RequestContext)
    context.request_id.return_value = "123"

    state = TransferAgentState(
        {TransferAgentStateFields.MESSAGES: [HumanMessage(content="test message")]}
    )
    config = {
        CONFIGURABLE_CONTEXT_KEY: {
            PENDING_RESPONSE_KEY: [],
            CONTEXT_KEY: context,
        }
    }

    llm.ainvoke.return_value = AIMessage(content="LLM response")

    with patch.object(agent, "get_agent", return_value=llm):
        result = await agent(state, config)

    assert len(result[TransferAgentStateFields.MESSAGES]) == 1
    assert isinstance(result[TransferAgentStateFields.MESSAGES][0], AIMessage)
    assert result[TransferAgentStateFields.MESSAGES][0].content == "LLM response"


@pytest.mark.asyncio
async def test_get_agent():
    prompt_srv = MagicMock()
    mock_llm = MagicMock()
    controller = MoneyTransferAgent(prompt_srv, mock_llm)
    mock_ctx = MagicMock(RequestContext)
    mock_prompt = MagicMock(
        tmpl=MessagesPlaceholder(variable_name="fake"), llm_model=mock_llm
    )
    prompt_srv.get_prompt = AsyncMock(return_value=mock_prompt)
    mock_llm.bind_tools = MagicMock(return_value=MagicMock(Runnable))

    agent = await controller.get_agent(mock_ctx)

    assert controller.ready is True
    assert agent is not None
