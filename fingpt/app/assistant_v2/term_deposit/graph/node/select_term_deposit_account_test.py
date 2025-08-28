import pytest

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, USER_CHOICE_ID_KEY
from app.assistant_v2.term_deposit.graph.node.select_term_deposit_account import (
    select_term_deposit_account_func,
)
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.entity import TermDepositAccount, TermUnit


@pytest.mark.asyncio
async def test_select_term_deposit_account(agent_config):
    # Mock the state and config
    state = {
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
                interest_rate=1.5,
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
        }
    }
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})
    config_data[USER_CHOICE_ID_KEY] = "td_account_1"

    # Call the function
    output = await select_term_deposit_account_func(state, agent_config)

    # Assertions
    assert TermDepositAgentStateFields.MESSAGES in output
    assert (
        output[TermDepositAgentStateFields.MESSAGES][0].content
        == "Selected term deposit account: test term deposit account 1 "
        "with deposit amount is 6000.0$"
    )
    assert TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS in output
    assert (
        list(output[TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS].values())[0].id
        == "td_account_1"
    )
    assert TermDepositAgentStateFields.RESUME_NODE in output
    assert output[TermDepositAgentStateFields.RESUME_NODE] is None


@pytest.mark.asyncio
async def test_select_account_no_choice(agent_config):
    # Mock the state and config
    state = {
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
        }
    }
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})
    config_data[USER_CHOICE_ID_KEY] = ""

    # Call the function and expect an assertion error
    with pytest.raises(AssertionError, match="User choice is empty"):
        await select_term_deposit_account_func(state, agent_config)
