import pytest
from langchain_core.messages import HumanMessage

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, PENDING_RESPONSE_KEY
from app.assistant_v2.term_deposit.graph.node.available_term_deposit_account import (
    available_term_deposit_account_func,
)
from app.assistant_v2.term_deposit.graph.node.select_term_deposit_account import (
    select_term_deposit_account_node,
)
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.entity import TermDepositAccount, TermUnit


@pytest.mark.asyncio
async def test_available_term_deposit_account(agent_config):
    # Mock the state and config
    state = {
        TermDepositAgentStateFields.MESSAGES: [HumanMessage(content="test message")],
        TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS: {
            "td_account_1": TermDepositAccount(
                id="td_account_1",
                name="test term deposit account 1",
                interest_rate=1.25,
                term_number=6,
                term_unit=TermUnit("M"),
                maturity_date="test_maturity_date_1",
                start_date="test_start_date_1",
                bban="test_bban_1",
                deposit_amount=6000,
                maturity_earn=0.0,
                is_renewable=True,
                is_mature=True,
            ),
            "td_account_2": TermDepositAccount(
                id="td_account_2",
                name="test term deposit account 2",
                interest_rate=1.6,
                term_number=1,
                term_unit=TermUnit("Y"),
                maturity_date="test_maturity_date_2",
                start_date="test_start_date_2",
                bban="test_bban_2",
                deposit_amount=10000,
                maturity_earn=0.0,
                is_renewable=True,
                is_mature=True,
            ),
        },
    }

    # Call the function
    output = await available_term_deposit_account_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})

    # Assertions
    assert TermDepositAgentStateFields.RESUME_NODE in output
    assert (
        output[TermDepositAgentStateFields.RESUME_NODE]
        == select_term_deposit_account_node
    )
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert config_data[PENDING_RESPONSE_KEY][0].action == "SHOW_CHOICES"
    assert len(config_data[PENDING_RESPONSE_KEY][0].metadata.choices) == 2
    assert config_data[PENDING_RESPONSE_KEY][0].metadata.choices[0].is_enabled
    assert config_data[PENDING_RESPONSE_KEY][0].metadata.choices[1].is_enabled
