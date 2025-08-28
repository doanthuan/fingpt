from unittest.mock import MagicMock

import pytest

from app.assistant_v2.constant import USER_CHOICE_ID_KEY
from app.assistant_v2.transaction.graph.node.select_beneficiary import (
    select_beneficiary_func,
)
from app.assistant_v2.transaction.state import TransactionAgentStateFields
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.entity import Transaction


@pytest.mark.asyncio
async def test_select_beneficiary_func_success(mocker):
    # Mocking the dependencies
    mocker.patch(
        "app.assistant_v2.transaction.graph.node.select_beneficiary.extract_config",
        return_value=(
            {USER_CHOICE_ID_KEY: "12345"},
            MagicMock(),
            MagicMock(),
        ),
    )
    state = {
        TransactionAgentStateFields.PROCESSED_TRANSACTIONS: {
            "12345": [
                Transaction(
                    account_id="12345",
                    execution_date="2023-01-01",
                    currency="USD",
                    counterparty_account="12345",
                    counterparty_name="test_name",
                    amount=100.0,
                    transaction_type="Deposit",
                )
            ]
        }
    }
    config = MagicMock()

    # Run the function
    result = await select_beneficiary_func(state, config)

    # Assertions
    assert (
        result[TransactionAgentStateFields.MESSAGES][0].content
        == "My selected beneficiary is: test_name"
    )
    assert (
        result[TransactionAgentStateFields.CONFIRMED_TRANSACTIONS]
        == state[TransactionAgentStateFields.PROCESSED_TRANSACTIONS]["12345"]
    )
    assert result[TransactionAgentStateFields.PROCESSED_TRANSACTIONS] == []
    assert result[TransferAgentStateFields.RESUME_NODE] is None


@pytest.mark.asyncio
async def test_select_beneficiary_func_no_choice(mocker):
    # Mocking the dependencies
    mocker.patch(
        "app.assistant_v2.transaction.graph.node.select_beneficiary.extract_config",
        return_value=(
            {USER_CHOICE_ID_KEY: ""},
            MagicMock(),
            MagicMock(),
        ),
    )
    state = {
        TransactionAgentStateFields.PROCESSED_TRANSACTIONS: {
            "12345": [
                Transaction(
                    account_id="12345",
                    execution_date="2023-01-01",
                    currency="USD",
                    counterparty_account="12345",
                    counterparty_name="test_name",
                    amount=100.0,
                    transaction_type="Deposit",
                )
            ]
        }
    }
    config = MagicMock()

    # Run the function and expect an exception
    with pytest.raises(AssertionError, match="User choice is empty"):
        await select_beneficiary_func(state, config)


@pytest.mark.asyncio
async def test_select_beneficiary_func_invalid_choice(mocker):
    # Mocking the dependencies
    mocker.patch(
        "app.assistant_v2.transaction.graph.node.select_beneficiary.extract_config",
        return_value=(
            {USER_CHOICE_ID_KEY: "invalid_id"},
            MagicMock(),
            MagicMock(),
        ),
    )
    state = {
        TransactionAgentStateFields.PROCESSED_TRANSACTIONS: {
            "12345": [
                Transaction(
                    account_id="12345",
                    execution_date="2023-01-01",
                    currency="USD",
                    counterparty_account="12345",
                    counterparty_name="test_name",
                    amount=100.0,
                    transaction_type="Deposit",
                )
            ]
        }
    }
    config = MagicMock()

    # Run the function and expect an exception
    with pytest.raises(Exception, match="Beneficiary with id invalid_id not found"):
        await select_beneficiary_func(state, config)
