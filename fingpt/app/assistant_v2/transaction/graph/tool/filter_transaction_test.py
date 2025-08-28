import json
from unittest.mock import AsyncMock, patch

import pytest

from app.assistant_v2.transaction.graph.tool.filter_transaction import (
    _filter_transaction,
)
from app.assistant_v2.transaction.state import (
    TransactionAgentState,
    TransactionAgentStateFields,
)
from app.entity import Transaction


@pytest.mark.asyncio
async def test_filter_transaction_valid_search_term():
    search_term = "Uber"
    config = AsyncMock()
    config_data = {"some": "config"}
    ctx = AsyncMock()
    logger = AsyncMock()
    transactions = [
        AsyncMock(
            counterparty_account="123",
            counterparty_name="Uber",
            dict=lambda: {"amount": 100},
        ),
        AsyncMock(
            counterparty_account="123",
            counterparty_name="Uber",
            dict=lambda: {"amount": 200},
        ),
    ]

    with patch(
        "app.assistant_v2.transaction.graph.tool.filter_transaction.extract_config",
        return_value=(config_data, ctx, logger),
    ), patch(
        "app.assistant_v2.transaction.graph.tool.filter_transaction.extract_bb_retail_api_config",
        return_value=config_data,
    ), patch(
        "app.assistant_v2.transaction.graph.tool.filter_transaction.filter_transactions",
        return_value=transactions,
    ):

        result = await _filter_transaction(search_term, config, {})
        result_data = json.loads(result)

        assert "123-Uber" in result_data
        assert len(result_data["123-Uber"]) == 2
        assert result_data["123-Uber"][0]["amount"] == 100
        assert result_data["123-Uber"][1]["amount"] == 200


@pytest.mark.asyncio
async def test_filter_transaction_short_search_term():
    search_term = "Ub"
    config = AsyncMock()
    config_data = {"some": "config"}
    ctx = AsyncMock()
    logger = AsyncMock()
    transactions = [
        AsyncMock(
            counterparty_account="123",
            counterparty_name="Uber",
            dict=lambda: {"amount": 100},
        ),
    ]

    with patch(
        "app.assistant_v2.transaction.graph.tool.filter_transaction.extract_config",
        return_value=(config_data, ctx, logger),
    ), patch(
        "app.assistant_v2.transaction.graph.tool.filter_transaction.extract_bb_retail_api_config",
        return_value=config_data,
    ), patch(
        "app.assistant_v2.transaction.graph.tool.filter_transaction.filter_transactions",
        return_value=transactions,
    ):

        result = await _filter_transaction(search_term, config, {})
        result_data = json.loads(result)

        assert "123-Uber" in result_data
        assert len(result_data["123-Uber"]) == 1
        assert result_data["123-Uber"][0]["amount"] == 100


@pytest.mark.asyncio
async def test_filter_transaction_no_transactions():
    search_term = "NonExistent"
    config = AsyncMock()
    config_data = {"some": "config"}
    ctx = AsyncMock()
    logger = AsyncMock()
    transactions = []

    with patch(
        "app.assistant_v2.transaction.graph.tool.filter_transaction.extract_config",
        return_value=(config_data, ctx, logger),
    ), patch(
        "app.assistant_v2.transaction.graph.tool.filter_transaction.extract_bb_retail_api_config",
        return_value=config_data,
    ), patch(
        "app.assistant_v2.transaction.graph.tool.filter_transaction.filter_transactions",
        return_value=transactions,
    ):

        result = await _filter_transaction(search_term, config, {})
        result_data = json.loads(result)

        assert result_data == {}


async def test_filter_transaction_with_selected():
    search_term = "Uber"
    state = TransactionAgentState(
        {
            TransactionAgentStateFields.CONFIRMED_TRANSACTIONS: [
                Transaction(
                    account_id="123",
                    execution_date="2021-01-01",
                    transaction_type="debit",
                    amount=100,
                    currency="USD",
                    counterparty_account="456",
                    counterparty_name="Uber",
                )
            ],
        }
    )
    config = AsyncMock()
    config_data = {"some": "config"}
    ctx = AsyncMock()
    logger = AsyncMock()
    transactions = [
        AsyncMock(
            counterparty_account="123",
            counterparty_name="Uber",
            dict=lambda: {"amount": 100},
        ),
        AsyncMock(
            counterparty_account="123",
            counterparty_name="Uber",
            dict=lambda: {"amount": 200},
        ),
    ]

    with patch(
        "app.assistant_v2.transaction.graph.tool.filter_transaction.extract_config",
        return_value=(config_data, ctx, logger),
    ), patch(
        "app.assistant_v2.transaction.graph.tool.filter_transaction.extract_bb_retail_api_config",
        return_value=config_data,
    ), patch(
        "app.assistant_v2.transaction.graph.tool.filter_transaction.filter_transactions",
        return_value=transactions,
    ):

        result = await _filter_transaction(search_term, config, state)
        result_data = json.loads(result)

        assert "selected_beneficiary" in result_data
        assert len(result_data["selected_beneficiary"]) == 1
