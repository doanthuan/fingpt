import json
from unittest.mock import AsyncMock, patch

import pytest

from app.assistant_v2.term_deposit.graph.tool.get_accounts import _get_account
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.entity import ActiveAccount


@pytest.mark.asyncio
async def test_get_account_success(agent_config):
    # Mock the list_accounts function
    accounts = [
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
    mock_accounts = AsyncMock(return_value=accounts)
    state = {TermDepositAgentStateFields.DEPOSIT_AMOUNT: 100}
    with patch(
        "app.assistant_v2.term_deposit.graph.tool.get_accounts.list_accounts",
        mock_accounts,
    ):
        result = await _get_account(state, agent_config)

        # Assertions
        result_list = eval(result)
        result_accounts = [
            ActiveAccount(**json.loads(account)) for account in result_list
        ]
        assert result_accounts == accounts


@pytest.mark.asyncio
async def test_get_account_failure(agent_config):
    # Mock the list_accounts function to raise an exception
    with patch(
        "app.assistant_v2.term_deposit.graph.tool.get_accounts.list_accounts",
        side_effect=Exception("API error"),
    ):
        state = {TermDepositAgentStateFields.DEPOSIT_AMOUNT: 100}
        # Call the function and expect an exception
        with pytest.raises(Exception, match="API error"):
            await _get_account(state, agent_config)
