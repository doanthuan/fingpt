from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from app.assistant_v2.constant import PENDING_RESPONSE_KEY, THREAD_ID_KEY
from app.assistant_v2.transaction.graph.node.generate_chart_data import (
    _create_transaction_report_data,
    generate_chart_data_func,
)
from app.assistant_v2.transaction.state import TransactionAgentStateFields
from app.entity import Transaction


async def test_generate_chart_data_func(mocker):
    # Mocking the dependencies
    mocker.patch(
        "app.assistant_v2.transaction.graph.node.generate_chart_data.extract_config",
        return_value=(
            {THREAD_ID_KEY: "thread_id", PENDING_RESPONSE_KEY: []},
            MagicMock(),
            MagicMock(),
        ),
    )
    state = {
        TransactionAgentStateFields.CONFIRMED_TRANSACTIONS: [
            Transaction(
                account_id="id_1",
                counterparty_name="test",
                counterparty_account="12345",
                execution_date="2023-01-15",
                amount=100.0,
                transaction_type="Deposit",
                currency="USD",
            ),
            Transaction(
                account_id="id_2",
                counterparty_name="test_2",
                counterparty_account="12345",
                execution_date="2023-01-20",
                amount=50.0,
                transaction_type="Withdrawal",
                currency="USD",
            ),
        ],
        TransactionAgentStateFields.MESSAGES: [AIMessage(content="test content")],
    }
    config = MagicMock()

    # Run the function
    result = await generate_chart_data_func(state, config)

    # Assertions
    assert TransactionAgentStateFields.MESSAGES in result
    assert TransactionAgentStateFields.CONFIRMED_TRANSACTIONS in result
    assert result[TransactionAgentStateFields.CONFIRMED_TRANSACTIONS] == []


def test_create_transaction_report_data():
    transactions = [
        Transaction(
            account_id="id_1",
            counterparty_name="test",
            counterparty_account="12345",
            execution_date="2023-01-15",
            amount=100.0,
            transaction_type="Deposit",
            currency="USD",
        ),
        Transaction(
            account_id="id_2",
            counterparty_name="test_2",
            counterparty_account="12345",
            execution_date="2023-01-20",
            amount=50.0,
            transaction_type="Withdrawal",
            currency="USD",
        ),
    ]

    expected_result = {"2023-01": {"pos": 100.0, "neg": -50.0, "total": 2}}

    result = _create_transaction_report_data(transactions)
    assert result == expected_result
