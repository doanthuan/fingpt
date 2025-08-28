from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables import Runnable

from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    PENDING_RESPONSE_KEY,
)
from app.assistant_v2.ticker.constant import (
    UNRECOGNIZED_SYMBOL_MESSAGE,
    UNSUPPORTED_SYMBOL_MESSAGE,
)
from app.assistant_v2.ticker.state import TickerAgentState, TickerAgentStateFields
from app.assistant_v2.ticker.symbol_identifier_agent import SymbolIdentifierAgent
from app.assistant_v2.ticker.tool.report_generator import report_generator_tool
from app.assistant_v2.ticker.tool.symbol_identifier import symbol_identifier_tool
from app.core.context import RequestContext
from app.entity import ChatRespAction


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def symbol_identifier_agent(prompt_service, mock_llm):
    return SymbolIdentifierAgent(prompt_srv=prompt_service, llm=mock_llm)


@pytest.fixture
def mock_state():
    return {TickerAgentStateFields.MESSAGES: ["Test message"]}


@pytest.mark.asyncio
async def test_call_with_pending_response(prompt_service, agent_config):
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=AIMessage(content="LLM response"))
    agent = SymbolIdentifierAgent(prompt_service, llm)
    config = agent_config.get(CONFIGURABLE_CONTEXT_KEY)
    config[PENDING_RESPONSE_KEY] = ["response"]
    state = TickerAgentState(
        {
            TickerAgentStateFields.MESSAGES: [HumanMessage(content="test message")],
        }
    )

    with patch.object(agent, "get_agent", return_value=llm):
        result = await agent(state, agent_config)

    assert result[TickerAgentStateFields.MESSAGES][0].content == "LLM response"


@pytest.mark.asyncio
async def test_call_with_tool_message_report_generator():
    prompt_srv = MagicMock()
    llm = MagicMock()
    agent = SymbolIdentifierAgent(prompt_srv, llm)
    context = MagicMock(RequestContext)
    context.request_id.return_value = "123"

    state = TickerAgentState(
        {
            TickerAgentStateFields.MESSAGES: [
                ToolMessage(
                    name=report_generator_tool.name,
                    content="report content",
                    tool_call_id="536",
                )
            ],
            TickerAgentStateFields.SYMBOL: "AAPL",
        }
    )
    config = {
        CONFIGURABLE_CONTEXT_KEY: {
            CONTEXT_KEY: context,
            PENDING_RESPONSE_KEY: [],
        }
    }

    result = await agent(state, config)

    assert len(result[TickerAgentStateFields.MESSAGES]) == 0
    assert (
        config[CONFIGURABLE_CONTEXT_KEY][PENDING_RESPONSE_KEY][-1].action
        == ChatRespAction.SHOW_TICKER_REPORT
    )


@pytest.mark.asyncio
async def test_call_with_llm_invocation():
    prompt_srv = MagicMock()
    llm = AsyncMock()
    agent = SymbolIdentifierAgent(prompt_srv, llm)
    context = MagicMock(RequestContext)
    context.request_id.return_value = "123"

    state = TickerAgentState(
        {TickerAgentStateFields.MESSAGES: [HumanMessage(content="test message")]}
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

    assert len(result[TickerAgentStateFields.MESSAGES]) == 1
    assert isinstance(result[TickerAgentStateFields.MESSAGES][0], AIMessage)
    assert result[TickerAgentStateFields.MESSAGES][0].content == "LLM response"


@pytest.mark.asyncio
async def test_call_with_report_generator_tool(
    symbol_identifier_agent, mock_state, agent_config
):
    mock_state[TickerAgentStateFields.MESSAGES] = [
        ToolMessage(
            name=report_generator_tool.name,
            content="Report content",
            tool_call_id="xxx",
        )
    ]
    mock_state[TickerAgentStateFields.SYMBOL] = "AAPL"
    result = await symbol_identifier_agent(mock_state, agent_config)
    assert result[TickerAgentStateFields.MESSAGES] == []
    assert result[TickerAgentStateFields.SYMBOL] == "AAPL"
    assert (
        agent_config[CONFIGURABLE_CONTEXT_KEY][PENDING_RESPONSE_KEY][-1].action
        == ChatRespAction.SHOW_TICKER_REPORT
    )


@pytest.mark.asyncio
async def test_call_with_symbol_identifier_tool_unknown(
    symbol_identifier_agent, mock_state, agent_config
):
    mock_state[TickerAgentStateFields.MESSAGES] = [
        ToolMessage(
            name=symbol_identifier_tool.name, content="UNKNOWN", tool_call_id="xxx"
        )
    ]
    result = await symbol_identifier_agent(mock_state, agent_config)
    assert result[TickerAgentStateFields.MESSAGES] == []
    assert result[TickerAgentStateFields.SYMBOL] is None
    assert (
        agent_config[CONFIGURABLE_CONTEXT_KEY][PENDING_RESPONSE_KEY][-1].response
        == UNRECOGNIZED_SYMBOL_MESSAGE
    )


@pytest.mark.asyncio
async def test_call_with_symbol_identifier_tool_invalid(
    symbol_identifier_agent, mock_state, agent_config
):
    mock_state[TickerAgentStateFields.MESSAGES] = [
        ToolMessage(
            name=symbol_identifier_tool.name, content="INVALID", tool_call_id="xxx"
        )
    ]
    result = await symbol_identifier_agent(mock_state, agent_config)
    assert result[TickerAgentStateFields.MESSAGES] == []
    assert result[TickerAgentStateFields.SYMBOL] is None
    assert agent_config[CONFIGURABLE_CONTEXT_KEY][PENDING_RESPONSE_KEY][
        -1
    ].response == UNSUPPORTED_SYMBOL_MESSAGE.format(symbol="INVALID")


@pytest.mark.asyncio
async def test_get_agent(symbol_identifier_agent, prompt_service, mock_llm):
    mock_ctx = MagicMock(RequestContext)
    mock_prompt = MagicMock(
        tmpl=MessagesPlaceholder(variable_name="fake"), llm_model=mock_llm
    )
    prompt_service.get_prompt = AsyncMock(return_value=mock_prompt)
    mock_llm.bind_tools = MagicMock(return_value=MagicMock(Runnable))

    agent = await symbol_identifier_agent.get_agent(mock_ctx)

    assert symbol_identifier_agent.ready is True
    assert agent is not None
    mock_llm.bind_tools.assert_called_once()
