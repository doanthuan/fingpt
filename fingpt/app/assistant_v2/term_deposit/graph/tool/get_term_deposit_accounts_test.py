import json
from unittest.mock import AsyncMock, patch

import pytest

from app.assistant_v2.term_deposit.graph.tool.get_term_deposit_accounts import (
    _get_term_deposit_accounts,
)
from app.entity import TermDepositAccount, TermUnit


@pytest.mark.asyncio
async def test_get_term_deposit_accounts_success(agent_config):
    # Mock the list_term_deposit_accounts function
    term_deposit_accounts = [
        TermDepositAccount(
            id="td_account_1",
            name="test term deposit account 1",
            interest_rate=1.25,
            term_number=6,
            term_unit=TermUnit("M"),
            maturity_date="2023-12-31",
            start_date="2023-06-01",
            bban="test_bban_1",
            deposit_amount=6000,
            maturity_earn=0.0,
            is_renewable=True,
            is_mature=True,
        ),
        TermDepositAccount(
            id="td_account_2",
            name="test term deposit account 2",
            interest_rate=1.5,
            term_number=1,
            term_unit=TermUnit("Y"),
            maturity_date="2024-12-31",
            start_date="2023-12-31",
            bban="test_bban_2",
            deposit_amount=10000,
            maturity_earn=0.0,
            is_renewable=True,
            is_mature=True,
        ),
    ]
    mock_accounts = AsyncMock(return_value=term_deposit_accounts)
    with patch(
        "app.assistant_v2.term_deposit.graph.tool.get_term_deposit_accounts.list_term_deposit_accounts",
        mock_accounts,
    ):
        result = await _get_term_deposit_accounts("", agent_config)

        # Assertions
        result_list = eval(result)
        result_accounts = [
            TermDepositAccount(**json.loads(account)) for account in result_list
        ]
        assert result_accounts == term_deposit_accounts


@pytest.mark.asyncio
async def test_get_term_deposit_accounts_failure(agent_config):
    # Mock the list_term_deposit_accounts function to raise an exception
    with patch(
        "app.assistant_v2.term_deposit.graph.tool.get_term_deposit_accounts.list_term_deposit_accounts",
        side_effect=Exception("API error"),
    ):
        # Call the function and expect an exception
        with pytest.raises(Exception, match="API error"):
            await _get_term_deposit_accounts("", agent_config)
