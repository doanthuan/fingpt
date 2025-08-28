import pytest
from langchain_core.messages import AIMessage, ToolCall

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, LLM_MODEL_KEY
from app.assistant_v2.primary.constant import (
    ENTER_CARD_SUBGRAPH_NODE,
    ENTER_TERM_DEPOSIT_SUBGRAPH_NODE,
    ENTER_TICKER_AGENT_NODE,
    ENTER_TRANSACTION_AGENT_NODE,
    ENTER_TRANSFER_AGENT_NODE,
    PREPARE_RESPONSE_NODE,
    PRIMARY_ASSISTANT_NODE,
    RETURN_CONTROL_NODE,
    TICKER_AGENT_TOOLS_NODE,
    TRANSACTION_AGENT_TOOLS_NODE,
    TRANSFER_AGENT_TOOLS_NODE,
)
from app.assistant_v2.primary.graph import AssistantGraph
from app.assistant_v2.primary.state import AssistantState
from app.assistant_v2.primary.tool.to_card_flow import ToCardFlow
from app.assistant_v2.primary.tool.to_term_deposit_flow import ToTermDepositFlow
from app.assistant_v2.primary.tool.to_ticker_agent import ToTickerAgent
from app.assistant_v2.primary.tool.to_transaction_agent import ToTransactionAgent
from app.assistant_v2.primary.tool.to_transfer_agent import ToTransferAgent
from app.assistant_v2.util.complete_or_escalate import CompleteOrEscalateTool


@pytest.fixture
def graph(agent_config, prompt_service):
    llm = agent_config[CONFIGURABLE_CONTEXT_KEY][LLM_MODEL_KEY]
    return AssistantGraph(prompt_service, llm)


def test_route_ticker_agent_to_tools_return_control(graph):
    tool1 = ToolCall(id="1", name=CompleteOrEscalateTool.__name__, args={})
    ai_tools_call_message = AIMessage(content="", tool_calls=[tool1])
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_ticker_agent_to_tools(state)
    assert output == RETURN_CONTROL_NODE


def test_route_ticker_agent_to_ticker_node(graph):
    tool = ToolCall(id="1", name="TickerTool", args={})
    ai_tools_call_message = AIMessage(content="", tool_calls=[tool])
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_ticker_agent_to_tools(state)
    assert output == TICKER_AGENT_TOOLS_NODE


def test_route_ticker_agent_to_end(graph):
    ai_tools_call_message = AIMessage(content="")
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_ticker_agent_to_tools(state)
    assert output == PREPARE_RESPONSE_NODE


def test_route_transaction_agent_to_tools(graph):
    tool1 = ToolCall(id="1", name=CompleteOrEscalateTool.__name__, args={})
    ai_tools_call_message = AIMessage(content="", tool_calls=[tool1])
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_transaction_agent_to_tools(state)
    assert output == RETURN_CONTROL_NODE


def test_route_transaction_agent_to_end(graph):
    ai_tools_call_message = AIMessage(content="")
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_transaction_agent_to_tools(state)
    assert output == PREPARE_RESPONSE_NODE


def test_rout_transaction_agent_to_subgraph(graph):
    tool = ToolCall(id="1", name="TransactionTool", args={})
    ai_tools_call_message = AIMessage(content="", tool_calls=[tool])
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_transaction_agent_to_tools(state)
    assert output == TRANSACTION_AGENT_TOOLS_NODE


def test_route_transfer_agent_to_tools(graph):
    tool1 = ToolCall(id="1", name=CompleteOrEscalateTool.__name__, args={})
    ai_tools_call_message = AIMessage(content="", tool_calls=[tool1])
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_transfer_agent_to_tools(state)
    assert output == RETURN_CONTROL_NODE


def test_route_transfer_agent_to_end(graph):
    ai_tools_call_message = AIMessage(content="")
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_transfer_agent_to_tools(state)
    assert output == PREPARE_RESPONSE_NODE


def test_route_transfer_agent_to_subgraph(graph):
    tool = ToolCall(id="1", name="TransferTool", args={})
    ai_tools_call_message = AIMessage(content="", tool_calls=[tool])
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_transfer_agent_to_tools(state)
    assert output == TRANSFER_AGENT_TOOLS_NODE


def test_route_primary_assistant_to_tools_end(graph):
    ai_tools_call_message = AIMessage(content="")
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_primary_assistant_to_tools(state)
    assert output == PREPARE_RESPONSE_NODE


def test_route_primary_assistant_to_ticker(graph):
    tool = ToolCall(id="1", name=ToTickerAgent.__name__, args={})
    ai_tools_call_message = AIMessage(content="", tool_calls=[tool])
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_primary_assistant_to_tools(state)
    assert output == ENTER_TICKER_AGENT_NODE


def test_route_primary_assistant_to_transaction(graph):
    tool = ToolCall(id="1", name=ToTransactionAgent.__name__, args={})
    ai_tools_call_message = AIMessage(content="", tool_calls=[tool])
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_primary_assistant_to_tools(state)
    assert output == ENTER_TRANSACTION_AGENT_NODE


def test_route_primary_assistant_to_transfer(graph):
    tool = ToolCall(id="1", name=ToTransferAgent.__name__, args={})
    ai_tools_call_message = AIMessage(content="", tool_calls=[tool])
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_primary_assistant_to_tools(state)
    assert output == ENTER_TRANSFER_AGENT_NODE


def test_direct_workflow_router(graph):
    state = AssistantState(controller_stack=["some_tool"])
    output1 = AssistantGraph.direct_workflow_router(state)
    state = AssistantState(controller_stack=[])
    output2 = AssistantGraph.direct_workflow_router(state)
    assert output1 == "some_tool"
    assert output2 == PRIMARY_ASSISTANT_NODE


def test_router_term_deposit_to_tools():
    tool = ToolCall(id="1", name=ToTermDepositFlow.__name__, args={})
    ai_tools_call_message = AIMessage(content="", tool_calls=[tool])
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_term_deposit_controller_to_tools(state)
    assert output == ENTER_TERM_DEPOSIT_SUBGRAPH_NODE


def test_router_term_deposit_to_end():
    ai_tools_call_message = AIMessage(content="")
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_term_deposit_controller_to_tools(state)
    assert output == PREPARE_RESPONSE_NODE


def test_router_term_deposit_to_return_control():
    tool = ToolCall(id="1", name=CompleteOrEscalateTool.__name__, args={})
    ai_tools_call_message = AIMessage(content="", tool_calls=[tool])
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_term_deposit_controller_to_tools(state)
    assert output == RETURN_CONTROL_NODE


def test_router_card_to_tools():
    tool = ToolCall(id="1", name=ToCardFlow.__name__, args={})
    ai_tools_call_message = AIMessage(content="", tool_calls=[tool])
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_card_controller_to_tools(state)
    assert output == ENTER_CARD_SUBGRAPH_NODE


def test_router_card_to_end():
    ai_tools_call_message = AIMessage(content="")
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_card_controller_to_tools(state)
    assert output == PREPARE_RESPONSE_NODE


def test_router_card_to_return_control():
    tool = ToolCall(id="1", name=CompleteOrEscalateTool.__name__, args={})
    ai_tools_call_message = AIMessage(content="", tool_calls=[tool])
    state = AssistantState(messages=[ai_tools_call_message])
    output = AssistantGraph.route_card_controller_to_tools(state)
    assert output == RETURN_CONTROL_NODE
