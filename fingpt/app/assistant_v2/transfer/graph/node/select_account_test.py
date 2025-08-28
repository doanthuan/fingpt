import pytest

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, USER_CHOICE_ID_KEY
from app.assistant_v2.transfer.graph.node.select_account import select_account_func
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.entity import ActiveAccount


@pytest.mark.asyncio
async def test_select_account(agent_config):
    # Mock the state and config
    state = {
        TransferAgentStateFields.ACTIVE_ACCOUNTS: [
            ActiveAccount(
                id="account_1",
                name="test account 1",
                product_type="test product",
                available_balance=1000,
                identifications=None,
                currency="USD",
            ),
            ActiveAccount(
                id="account_2",
                name="test account 2",
                product_type="test product",
                available_balance=500,
                identifications=None,
                currency="USD",
            ),
        ]
    }
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})
    config_data[USER_CHOICE_ID_KEY] = "account_1"

    # Call the function
    output = await select_account_func(state, agent_config)

    # Assertions
    assert TransferAgentStateFields.MESSAGES in output
    assert (
        output[TransferAgentStateFields.MESSAGES][0].content
        == "My select account is id: account_1, name: test account 1"
    )
    assert TransferAgentStateFields.ACTIVE_ACCOUNTS in output
    assert output[TransferAgentStateFields.SELECTED_ACCOUNT].id == "account_1"
    assert TransferAgentStateFields.RESUME_NODE in output
    assert output[TransferAgentStateFields.RESUME_NODE] is None


@pytest.mark.asyncio
async def test_select_account_no_choice(agent_config):
    # Mock the state and config
    state = {
        TransferAgentStateFields.ACTIVE_ACCOUNTS: [
            ActiveAccount(
                id="account_1",
                name="test account 1",
                product_type="test product",
                available_balance=1000,
                identifications=None,
                currency="USD",
            )
        ]
    }
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})
    config_data[USER_CHOICE_ID_KEY] = ""

    # Call the function and expect an assertion error
    with pytest.raises(AssertionError, match="User choice is empty"):
        await select_account_func(state, agent_config)
