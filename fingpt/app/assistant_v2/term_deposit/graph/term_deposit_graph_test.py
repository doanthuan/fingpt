from unittest.mock import MagicMock

import pytest
from langchain_core.runnables import RunnableConfig

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, CONTEXT_KEY
from app.assistant_v2.term_deposit.graph.term_deposit_graph import TermDepositGraph
from app.assistant_v2.term_deposit.state import (
    TermDepositAgentState,
    TermDepositAgentStateFields,
)


@pytest.mark.asyncio
async def test_start_node_fnc():
    graph = TermDepositGraph()

    # Mock context
    mock_context = MagicMock()
    mock_context.logger = MagicMock()

    # Create config with mock context
    config = RunnableConfig()
    config[CONFIGURABLE_CONTEXT_KEY] = {CONTEXT_KEY: mock_context}

    # Test case where action is "get_offer"
    state = TermDepositAgentState()
    state[TermDepositAgentStateFields.ACTION] = "get_offer"
    result = await graph.start_node_fnc(state, config)
    assert result == {
        TermDepositAgentStateFields.MESSAGES: []
    }, "Expected state to be returned with empty messages when action is 'get_offer'"

    # Test case where action is not "get_offer"
    state = TermDepositAgentState()
    state[TermDepositAgentStateFields.ACTION] = "other_action"
    result = await graph.start_node_fnc(state, config)
    assert result == {
        TermDepositAgentStateFields.MESSAGES: []
    }, "Expected state to be processed by BaseGraph.start_node_fnc when action is not 'get_offer'"
