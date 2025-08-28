from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from app.assistant_v2.common.base_agent_state import BaseAgentState
from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    PENDING_RESPONSE_KEY,
    PROMPT_SERVICE_KEY,
    USER_QUERY_KEY,
)
from app.assistant_v2.primary.constant import CONTROLLER_ENTER_CONTENT
from app.assistant_v2.primary.node import (
    _summary_previous_messages,
    controller_enter_node,
    controller_exit_node,
    delete_message,
    prepare_response_node,
    subgraph_enter_node,
    wrap_agent_node,
)
from app.assistant_v2.primary.state import AssistantStateFields
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.assistant_v2.transaction.state import TransactionAgentStateFields
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.core import RequestContext
from app.entity.assistant import AssistantStatus
from app.prompt.prompt_service import PromptService


@pytest.mark.asyncio
async def test_controller_enter_node():
    state = {
        AssistantStateFields.MESSAGES: [
            MagicMock(tool_calls=[{"name": "test_assistant", "id": "tool_id"}])
        ],
        AssistantStateFields.CONTROLLER_STACK: [],
    }
    config = RunnableConfig()
    node = controller_enter_node("test_assistant", "test_controller")
    result = node(state, config)
    assert result[AssistantStateFields.MESSAGES][
        0
    ].content == CONTROLLER_ENTER_CONTENT.format(agent="test_controller")
    assert result[AssistantStateFields.CONTROLLER_STACK] == ["test_controller"]


@pytest.mark.asyncio
async def test_controller_exit_node():
    state = {
        AssistantStateFields.MESSAGES: [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "CompleteOrEscalateTool",
                        "id": "tool_id",
                        "args": {"reason": "test reason"},
                    }
                ],
            )
        ],
        AssistantStateFields.CONTROLLER_STACK: ["TERM_DEPOSIT_CONTROLLER"],
    }
    with patch(
        "app.assistant_v2.primary.node._summary_previous_messages",
        AsyncMock(return_value=AIMessage(content="Fake summary")),
    ) as mock_summary:
        result = await controller_exit_node(
            state, {"configurable": {"ctx": MagicMock(), USER_QUERY_KEY: "test query"}}
        )
    assert result[AssistantStateFields.MESSAGES][0].content == "Fake summary"
    mock_summary.assert_called_once()
    assert result[AssistantStateFields.CONTROLLER_STACK] == []


@pytest.mark.asyncio
async def test_summary_previous_messages():
    state = BaseAgentState()
    state[AssistantStateFields.MESSAGES] = [
        MagicMock(id="1", content="User message 1", tool_calls=None),
        MagicMock(id="2", content="AI message 1", tool_calls=None),
        MagicMock(id="3", content="User message 2", tool_calls=None),
        MagicMock(id="4", content="AI message 2", tool_calls=None),
    ]
    state[AssistantStateFields.LAST_SUMMARY_MESSAGE_ID] = "2"

    config = {
        CONFIGURABLE_CONTEXT_KEY: {
            CONTEXT_KEY: MagicMock(
                RequestContext, logger=MagicMock(info=MagicMock(), debug=MagicMock())
            ),
            PROMPT_SERVICE_KEY: MagicMock(PromptService),
        }
    }

    config_data = config[CONFIGURABLE_CONTEXT_KEY]
    fake_tmpl = ChatPromptTemplate.from_messages([("system", "nothing")])
    config_data[PROMPT_SERVICE_KEY].get_prompt = AsyncMock(
        return_value=MagicMock(
            tmpl=fake_tmpl,
            label="",
            llm_model=FakeListChatModel(responses=["Summary response"]),
        )
    )

    result = await _summary_previous_messages(state, config)

    assert result.content == "Summary response"
    config_data[CONTEXT_KEY].logger().info.assert_called_with(
        "Summarizing previous messages from 2..."
    )
    config_data[CONTEXT_KEY].logger().debug.assert_called()


def test_prepare_response_node():
    state = {AssistantStateFields.MESSAGES: [MagicMock()]}
    config = RunnableConfig()
    config[CONFIGURABLE_CONTEXT_KEY] = {
        CONTEXT_KEY: MagicMock(logger=MagicMock(info=MagicMock())),
        PENDING_RESPONSE_KEY: "response",
    }
    result = prepare_response_node(state, config)
    assert result == state


@pytest.mark.asyncio
async def test_subgraph_enter_node():
    state = {
        AssistantStateFields.MESSAGES: [
            MagicMock(tool_calls=[{"name": "test_tool", "id": "tool_id"}])
        ]
    }
    config = RunnableConfig()
    node = subgraph_enter_node("test_subgraph")
    result = node(state, config)
    assert result[AssistantStateFields.MESSAGES][
        0
    ].content == CONTROLLER_ENTER_CONTENT.format(agent="test_subgraph")


@pytest.mark.asyncio
async def test_wrap_transaction_report_graph_node():
    state = {
        AssistantStateFields.MESSAGES: [MagicMock()],
        AssistantStateFields.TRANSACTION_REPORT_AGENT_STATE: {
            TransactionAgentStateFields.SEARCH_TERM: "search_term",
            TransactionAgentStateFields.PROCESSED_TRANSACTIONS: [],
            TransactionAgentStateFields.CONFIRMED_TRANSACTIONS: [],
            TransactionAgentStateFields.RESUME_NODE: "resume_node",
        },
    }
    transaction_agent = AsyncMock()
    transaction_agent.ainvoke.return_value = {
        TransactionAgentStateFields.PROCESSED_TRANSACTIONS: [],
        TransactionAgentStateFields.RESUME_NODE: "resume_node",
        TransactionAgentStateFields.MESSAGES: [MagicMock()],
    }
    node = await wrap_agent_node(
        transaction_agent,
        AssistantStateFields.TRANSACTION_REPORT_AGENT_STATE,
    )
    agent_config = {"configurable": {"user_query": "test query", "ctx": MagicMock()}}
    result = await node(state, agent_config)
    assert result[AssistantStateFields.STATUS] == AssistantStatus.WAIT_FOR_CHOICE


@pytest.mark.asyncio
async def test_wrap_transfer_graph_node():
    state = {
        AssistantStateFields.MESSAGES: [MagicMock()],
        AssistantStateFields.TRANSFER_AGENT_STATE: {
            TransferAgentStateFields.RECIPIENT_NAME: "recipient_name",
            TransferAgentStateFields.TRANSFER_AMOUNT: 100,
            TransferAgentStateFields.CONTACT_LIST: [],
            TransferAgentStateFields.ACTIVE_ACCOUNTS: [],
            TransferAgentStateFields.SELECTED_ACCOUNT: None,
            TransferAgentStateFields.SELECTED_CONTACT: None,
            TransferAgentStateFields.RESUME_NODE: "resume_node",
        },
    }
    transfer_agent = AsyncMock()
    transfer_agent.ainvoke.return_value = {
        TransferAgentStateFields.MESSAGES: [MagicMock()],
        TransferAgentStateFields.RECIPIENT_NAME: "recipient_name",
        TransferAgentStateFields.TRANSFER_AMOUNT: 100,
        TransferAgentStateFields.CONTACT_LIST: [],
        TransferAgentStateFields.ACTIVE_ACCOUNTS: [],
        TransferAgentStateFields.SELECTED_ACCOUNT: None,
        TransferAgentStateFields.SELECTED_CONTACT: None,
        TransferAgentStateFields.RESUME_NODE: "resume_node",
    }
    node = await wrap_agent_node(
        transfer_agent,
        AssistantStateFields.TRANSFER_AGENT_STATE,
    )
    agent_config = {"configurable": {"user_query": "test query", "ctx": MagicMock()}}
    result = await node(state, agent_config)
    assert result[AssistantStateFields.STATUS] == AssistantStatus.WAIT_FOR_CHOICE


@pytest.mark.asyncio
async def test_wrap_term_deposit_graph_node():
    state = {
        AssistantStateFields.MESSAGES: [HumanMessage(content="test message")],
        AssistantStateFields.TERM_DEPOSIT_AGENT_STATE: {
            TermDepositAgentStateFields.DEPOSIT_AMOUNT: 1000,
            TermDepositAgentStateFields.TERM_NUMBER: 12,
            TermDepositAgentStateFields.TERM_UNIT: "months",
            TermDepositAgentStateFields.ACTIVE_ACCOUNTS: {},
            TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS: {},
            TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS: {},
            TermDepositAgentStateFields.ACTION: "create",
            TermDepositAgentStateFields.RESUME_NODE: "resume_node",
        },
    }
    term_deposit_agent = AsyncMock()
    term_deposit_agent.ainvoke.return_value = {
        TermDepositAgentStateFields.MESSAGES: [
            HumanMessage(content="response message")
        ],
    }
    node = await wrap_agent_node(
        term_deposit_agent,
        AssistantStateFields.TERM_DEPOSIT_AGENT_STATE,
    )
    agent_config = {"configurable": {"user_query": "test query", "ctx": MagicMock()}}
    result = await node(state, agent_config)
    assert result[AssistantStateFields.STATUS] == AssistantStatus.WAIT_FOR_QUERY


@pytest.mark.asyncio
async def test_delete_message():
    # Setup initial state
    state = {
        AssistantStateFields.MESSAGES: [
            HumanMessage(id="1", content="Hello"),
            AIMessage(id="2", content="Hi there!"),
            HumanMessage(id="3", content="How are you?"),
        ],
        AssistantStateFields.LAST_SUMMARY_MESSAGE_ID: "2",
        AssistantStateFields.CONTROLLER_STACK: [],
    }

    config = {
        "configurable_context_key": {"context_key": MagicMock(logger=lambda: print)}
    }

    # Call the function
    result = await delete_message(state, config)

    # Verify the result
    expected_messages = [RemoveMessage(id="1")]
    assert result[AssistantStateFields.MESSAGES] == expected_messages
