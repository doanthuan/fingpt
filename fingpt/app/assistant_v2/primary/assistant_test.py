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
from app.assistant_v2.primary.assistant import Assistant
from app.assistant_v2.primary.state import AssistantState, AssistantStateFields
from app.core.context import RequestContext


@pytest.mark.asyncio
async def test_get_agent():
    prompt_srv = MagicMock()
    mock_llm = MagicMock()
    assistant = Assistant(prompt_srv, mock_llm)
    mock_ctx = MagicMock(RequestContext)
    mock_prompt = MagicMock(
        tmpl=MessagesPlaceholder(variable_name="fake"), llm_model=mock_llm
    )
    mock_prompt.tmpl = MessagesPlaceholder(variable_name="fake")
    prompt_srv.get_prompt = AsyncMock(return_value=mock_prompt)
    mock_llm.bind_tools = MagicMock(return_value=MagicMock(Runnable))

    agent = await assistant.get_agent(mock_ctx)

    assert assistant.ready is True
    assert agent is not None
    mock_llm.bind_tools.assert_called_once()


@pytest.mark.asyncio
async def test_call_with_pending_response():
    prompt_srv = MagicMock()
    llm = MagicMock()
    assistant = Assistant(prompt_srv, llm)

    state = AssistantState(
        {AssistantStateFields.MESSAGES: [HumanMessage(content="test message")]}
    )
    config = {
        CONFIGURABLE_CONTEXT_KEY: {
            PENDING_RESPONSE_KEY: ["response"],
            CONTEXT_KEY: MagicMock(RequestContext),
        }
    }

    result = await assistant(state, config)

    assert result == {AssistantStateFields.MESSAGES: []}


@pytest.mark.asyncio
async def test_call_with_llm_invocation():
    prompt_srv = MagicMock()
    llm = AsyncMock()
    assistant = Assistant(prompt_srv, llm)
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

    with patch.object(assistant, "get_agent", return_value=llm):
        result = await assistant(state, config)

    assert len(result[AssistantStateFields.MESSAGES]) == 1
    assert isinstance(result[AssistantStateFields.MESSAGES][0], AIMessage)
    assert result[AssistantStateFields.MESSAGES][0].content == "LLM response"


@pytest.mark.asyncio
async def test_call_with_exception():
    prompt_srv = MagicMock()
    llm = AsyncMock()
    assistant = Assistant(prompt_srv, llm)
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

    llm.ainvoke.side_effect = Exception("Test exception")

    with patch.object(assistant, "get_agent", return_value=llm):
        with pytest.raises(Exception, match="Test exception"):
            await assistant(state, config)
