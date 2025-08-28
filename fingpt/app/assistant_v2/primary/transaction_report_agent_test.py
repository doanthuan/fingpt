from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables import Runnable

from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    PENDING_RESPONSE_KEY,
)
from app.assistant_v2.primary.state import AssistantState, AssistantStateFields
from app.assistant_v2.primary.transaction_report_agent import TransactionReportAgent
from app.core.context import RequestContext


@pytest.mark.asyncio
async def test_call_with_valid_output():
    prompt_srv = MagicMock()
    llm = AsyncMock()
    agent = TransactionReportAgent(prompt_srv, llm)
    context = MagicMock(RequestContext)
    context.request_id.return_value = "123"

    state = AssistantState(
        {AssistantStateFields.MESSAGES: [HumanMessage(content="test message")]}
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

    assert len(result[AssistantStateFields.MESSAGES]) == 1
    assert isinstance(result[AssistantStateFields.MESSAGES][0], AIMessage)
    assert result[AssistantStateFields.MESSAGES][0].content == "LLM response"


@pytest.mark.asyncio
async def test_call_with_retry():
    prompt_srv = MagicMock()
    llm = AsyncMock()
    agent = TransactionReportAgent(prompt_srv, llm)
    context = MagicMock(RequestContext)
    context.request_id.return_value = "123"

    state = AssistantState(
        {AssistantStateFields.MESSAGES: [HumanMessage(content="test message")]}
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

    assert len(result[AssistantStateFields.MESSAGES]) == 1
    assert isinstance(result[AssistantStateFields.MESSAGES][0], AIMessage)
    assert result[AssistantStateFields.MESSAGES][0].content == "LLM response"


@pytest.mark.asyncio
async def test_get_agent():
    prompt_srv = MagicMock()
    mock_llm = MagicMock()
    controller = TransactionReportAgent(prompt_srv, mock_llm)
    mock_ctx = MagicMock(RequestContext)
    mock_prompt = MagicMock(
        tmpl=MessagesPlaceholder(variable_name="fake"), llm_model=mock_llm
    )
    prompt_srv.get_prompt = AsyncMock(return_value=mock_prompt)
    mock_llm.bind_tools = MagicMock(return_value=MagicMock(Runnable))

    agent = await controller.get_agent(mock_ctx)

    assert controller.ready is True
    assert agent is not None
