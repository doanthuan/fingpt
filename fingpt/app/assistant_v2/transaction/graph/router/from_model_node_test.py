import pytest
from langchain_core.messages import HumanMessage

from app.assistant_v2.transaction.graph.router.from_model_node import (
    router_from_model,
    to_end_edge,
    to_generate_chart_node,
    to_select_beneficiary_node,
    to_tool_edge,
)
from app.assistant_v2.transaction.state import TransactionAgentStateFields


@pytest.mark.asyncio
async def test_router_from_model_no_tool_calls_no_confirmed_no_processed():
    state = {
        TransactionAgentStateFields.MESSAGES: [
            HumanMessage(content="Test message", tool_calls=[])
        ],
        TransactionAgentStateFields.CONFIRMED_TRANSACTIONS: None,
        TransactionAgentStateFields.PROCESSED_TRANSACTIONS: None,
    }
    result = router_from_model(state)
    assert result == to_end_edge


@pytest.mark.asyncio
async def test_router_from_model_no_tool_calls_with_confirmed():
    state = {
        TransactionAgentStateFields.MESSAGES: [
            HumanMessage(content="Test message", tool_calls=[])
        ],
        TransactionAgentStateFields.CONFIRMED_TRANSACTIONS: ["transaction1"],
        TransactionAgentStateFields.PROCESSED_TRANSACTIONS: None,
    }
    result = router_from_model(state)
    assert result == to_generate_chart_node


@pytest.mark.asyncio
async def test_router_from_model_no_tool_calls_with_processed():
    state = {
        TransactionAgentStateFields.MESSAGES: [
            HumanMessage(content="Test message", tool_calls=[])
        ],
        TransactionAgentStateFields.CONFIRMED_TRANSACTIONS: None,
        TransactionAgentStateFields.PROCESSED_TRANSACTIONS: ["transaction1"],
    }
    result = router_from_model(state)
    assert result == to_select_beneficiary_node


@pytest.mark.asyncio
async def test_router_from_model_with_tool_calls():
    state = {
        TransactionAgentStateFields.MESSAGES: [
            HumanMessage(content="Test message", tool_calls=["tool_call"])
        ],
        TransactionAgentStateFields.CONFIRMED_TRANSACTIONS: None,
        TransactionAgentStateFields.PROCESSED_TRANSACTIONS: None,
    }
    result = router_from_model(state)
    assert result == to_tool_edge
