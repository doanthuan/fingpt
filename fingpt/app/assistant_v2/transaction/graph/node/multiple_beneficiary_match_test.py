from unittest.mock import MagicMock

from app.assistant_v2.constant import PENDING_RESPONSE_KEY, THREAD_ID_KEY
from app.assistant_v2.transaction.graph.node import select_beneficiary_node
from app.assistant_v2.transaction.graph.node.multiple_beneficiary_match import (
    multiple_beneficiary_match_func,
)
from app.assistant_v2.transaction.state import TransactionAgentStateFields
from app.entity import Transaction


async def test_multiple_beneficiary_match_func(mocker):
    # Mocking the dependencies
    mocker.patch(
        "app.assistant_v2.transaction.graph.node.multiple_beneficiary_match.extract_config",
        return_value=(
            {THREAD_ID_KEY: "thread_id", PENDING_RESPONSE_KEY: []},
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
            ],
            "67890": [
                Transaction(
                    account_id="67890",
                    execution_date="2023-01-01",
                    transaction_type="Deposit",
                    currency="USD",
                    amount=100.0,
                    counterparty_name="test_name_2",
                    counterparty_account="67890",
                )
            ],
        },
        TransactionAgentStateFields.MESSAGES: [MagicMock(content="test content")],
    }
    config = MagicMock()

    # Run the function
    result = await multiple_beneficiary_match_func(state, config)

    # Assertions
    assert TransactionAgentStateFields.RESUME_NODE in result
    assert result[TransactionAgentStateFields.RESUME_NODE] == select_beneficiary_node
