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
from app.assistant_v2.primary.state import AssistantState, AssistantStateFields
from app.assistant_v2.primary.term_deposit_controller import TermDepositController
from app.core.context import RequestContext


@pytest.mark.asyncio
async def test_call_with_pending_response():
    prompt_srv = MagicMock()
    llm = MagicMock()
    controller = TermDepositController(prompt_srv, llm)

    state = AssistantState(
        {AssistantStateFields.MESSAGES: [HumanMessage(content="test message")]}
    )
    config = {
        CONFIGURABLE_CONTEXT_KEY: {
            PENDING_RESPONSE_KEY: ["response"],
            CONTEXT_KEY: MagicMock(RequestContext),
        }
    }

    result = await controller(state, config)

    assert result == {AssistantStateFields.MESSAGES: []}


@pytest.mark.asyncio
async def test_call_with_user_choice():
    prompt_srv = MagicMock()
    llm = MagicMock()
    controller = TermDepositController(prompt_srv, llm)
    context = MagicMock(RequestContext)
    context.request_id.return_value = "123"

    state = AssistantState(
        {AssistantStateFields.MESSAGES: [HumanMessage(content="test message")]}
    )
    config = {
        CONFIGURABLE_CONTEXT_KEY: {
            USER_CHOICE_ID_KEY: "choice",
            CONTEXT_KEY: context,
        }
    }

    result = await controller(state, config)

    assert len(result[AssistantStateFields.MESSAGES]) == 1
    assert isinstance(result[AssistantStateFields.MESSAGES][0], AIMessage)
    assert (
        result[AssistantStateFields.MESSAGES][0].content == "Resume with user choice."
    )


@pytest.mark.asyncio
async def test_call_with_llm_invocation():
    prompt_srv = MagicMock()
    llm = AsyncMock()
    controller = TermDepositController(prompt_srv, llm)
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

    with patch.object(controller, "get_agent", return_value=llm):
        result = await controller(state, config)

    assert len(result[AssistantStateFields.MESSAGES]) == 1
    assert isinstance(result[AssistantStateFields.MESSAGES][0], AIMessage)
    assert result[AssistantStateFields.MESSAGES][0].content == "LLM response"


@pytest.mark.asyncio
async def test_get_agent():
    prompt_srv = MagicMock()
    mock_llm = MagicMock()
    controller = TermDepositController(prompt_srv, mock_llm)
    mock_ctx = MagicMock(RequestContext)
    mock_prompt = MagicMock(name="fake_prompt", llm_model=mock_llm)
    mock_prompt.tmpl = MessagesPlaceholder(variable_name="fake")
    prompt_srv.get_prompt = AsyncMock(return_value=mock_prompt)
    mock_llm.bind_tools = MagicMock(return_value=MagicMock(Runnable))

    agent = await controller.get_agent(mock_ctx)

    assert controller.ready is True
    assert agent is not None
    mock_llm.bind_tools.assert_called_once()
