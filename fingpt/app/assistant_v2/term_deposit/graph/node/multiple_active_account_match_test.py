import pytest
from langchain_core.messages import HumanMessage

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, PENDING_RESPONSE_KEY
from app.assistant_v2.term_deposit.graph.node.multiple_active_account_match import (
    multiple_active_account_match_func,
)
from app.assistant_v2.term_deposit.graph.node.select_account import select_account_node
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.entity import AccountIdentification, ActiveAccount


@pytest.mark.asyncio
async def test_multiple_active_account_match(agent_config):
    # Mock the state and config
    state = {
        TermDepositAgentStateFields.MESSAGES: [HumanMessage(content="test message")],
        TermDepositAgentStateFields.ACTIVE_ACCOUNTS: {
            "ac_1": ActiveAccount(
                id="ac_1",
                name="test account 1",
                product_type="test product",
                available_balance=1000,
                identifications=AccountIdentification(),
                currency="USD",
            ),
            "ac_2": ActiveAccount(
                id="ac_2",
                name="test account 2",
                product_type="test product",
                available_balance=500,
                identifications=AccountIdentification(),
                currency="USD",
            ),
            "ac_3": ActiveAccount(
                id="ac_3",
                name="test account 3",
                product_type="test product",
                available_balance=1500,
                identifications=AccountIdentification(),
                currency="USD",
            ),
        },
        TermDepositAgentStateFields.DEPOSIT_AMOUNT: 600,
    }

    # Call the function
    output = await multiple_active_account_match_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})

    # Assertions
    assert TermDepositAgentStateFields.RESUME_NODE in output
    assert output[TermDepositAgentStateFields.RESUME_NODE] == select_account_node
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert config_data[PENDING_RESPONSE_KEY][0].action == "SHOW_CHOICES"
    assert len(config_data[PENDING_RESPONSE_KEY][0].metadata.choices) == 3
    assert (
        config_data[PENDING_RESPONSE_KEY][0].metadata.choices[0].available_balance
        == 1500
    )
    assert config_data[PENDING_RESPONSE_KEY][0].metadata.choices[0].is_enabled
    assert config_data[PENDING_RESPONSE_KEY][0].metadata.choices[1].is_enabled
    assert not config_data[PENDING_RESPONSE_KEY][0].metadata.choices[2].is_enabled
