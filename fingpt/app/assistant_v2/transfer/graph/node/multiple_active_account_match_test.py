import pytest
from langchain_core.messages import HumanMessage

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, PENDING_RESPONSE_KEY
from app.assistant_v2.transfer.graph.node.multiple_active_account_match import (
    multiple_active_account_match_func,
)
from app.assistant_v2.transfer.graph.node.select_account import select_account_node
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.entity import AccountIdentification, ActiveAccount


@pytest.mark.asyncio
async def test_multiple_active_account_match(agent_config):
    # Mock the state and config
    state = {
        TransferAgentStateFields.MESSAGES: [HumanMessage(content="test message")],
        TransferAgentStateFields.ACTIVE_ACCOUNTS: [
            ActiveAccount(
                id="ac_1",
                name="test account 1",
                product_type="test product",
                available_balance=1000,
                identifications=AccountIdentification(),
                currency="USD",
            ),
            ActiveAccount(
                id="ac_2",
                name="test account 2",
                product_type="test product",
                available_balance=500,
                identifications=AccountIdentification(),
                currency="USD",
            ),
        ],
        TransferAgentStateFields.TRANSFER_AMOUNT: 600,
    }

    # Call the function
    output = await multiple_active_account_match_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})

    # Assertions
    assert TransferAgentStateFields.RESUME_NODE in output
    assert output[TransferAgentStateFields.RESUME_NODE] == select_account_node
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert config_data[PENDING_RESPONSE_KEY][0].action == "SHOW_CHOICES"
    assert len(config_data[PENDING_RESPONSE_KEY][0].metadata.choices) == 2
    assert config_data[PENDING_RESPONSE_KEY][0].metadata.choices[0].is_enabled
    assert not config_data[PENDING_RESPONSE_KEY][0].metadata.choices[1].is_enabled
