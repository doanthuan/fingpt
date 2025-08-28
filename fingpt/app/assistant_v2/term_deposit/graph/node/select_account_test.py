import pytest

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, USER_CHOICE_ID_KEY
from app.assistant_v2.term_deposit.graph.node.select_account import select_account_func
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.entity import AccountIdentification, ActiveAccount


@pytest.mark.asyncio
async def test_select_account(agent_config):
    # Mock the state and config
    state = {
        TermDepositAgentStateFields.ACTIVE_ACCOUNTS: {
            "account_1": ActiveAccount(
                id="account_1",
                name="test account 1",
                product_type="test product",
                available_balance=1000,
                identifications=AccountIdentification(),
                currency="USD",
            ),
            "account_2": ActiveAccount(
                id="account_2",
                name="test account 2",
                product_type="test product",
                available_balance=500,
                identifications=AccountIdentification(),
                currency="USD",
            ),
        }
    }
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})
    config_data[USER_CHOICE_ID_KEY] = "account_1"

    # Call the function
    output = await select_account_func(state, agent_config)

    # Assertions
    assert TermDepositAgentStateFields.MESSAGES in output
    assert (
        output[TermDepositAgentStateFields.MESSAGES][0].content
        == "Selected account: test account 1"
    )
    assert TermDepositAgentStateFields.ACTIVE_ACCOUNTS in output
    assert (
        list(output[TermDepositAgentStateFields.ACTIVE_ACCOUNTS].values())[0].id
        == "account_1"
    )
    assert TermDepositAgentStateFields.RESUME_NODE in output
    assert output[TermDepositAgentStateFields.RESUME_NODE] is None


@pytest.mark.asyncio
async def test_select_account_no_choice(agent_config):
    # Mock the state and config
    state = {
        TermDepositAgentStateFields.ACTIVE_ACCOUNTS: {
            "account_1": ActiveAccount(
                id="account_1",
                name="test account 1",
                product_type="test product",
                available_balance=1000,
                identifications=AccountIdentification(),
                currency="USD",
            )
        }
    }
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})
    config_data[USER_CHOICE_ID_KEY] = ""

    # Call the function and expect an assertion error
    with pytest.raises(AssertionError, match="User choice is empty"):
        await select_account_func(state, agent_config)
