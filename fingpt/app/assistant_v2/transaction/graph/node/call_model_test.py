from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate

from app.assistant_v2.constant import (
    LLM_MODEL_KEY,
    PENDING_RESPONSE_KEY,
    PROMPT_SERVICE_KEY,
    THREAD_ID_KEY,
)
from app.assistant_v2.transaction.constant import FILTER_TRANSACTION_TOOL_NAME
from app.assistant_v2.transaction.graph.node.call_model import (
    _chain_ainvoke,
    _parse_processed_transactions,
    call_model_func,
    extract_tool_messages,
)
from app.assistant_v2.transaction.state import TransactionAgentStateFields
from app.entity import ChatPrompt, Transaction
from app.prompt.prompt_service import PromptService


@pytest.mark.asyncio
async def test_call_model_func(agent_config):
    mock_message = MagicMock()
    mock_message.content = "Some test messages"
    state = {TransactionAgentStateFields.MESSAGES: [mock_message]}
    prompt_service = MagicMock(PromptService)
    mock_prompt = MagicMock(ChatPrompt)
    mock_prompt.tmpl = ChatPromptTemplate.from_messages(
        [("system", "test instruction with {{tool_names}}")]
    )
    prompt_service.get_prompt = AsyncMock(return_value=mock_prompt)
    config_data = {
        PROMPT_SERVICE_KEY: prompt_service,
        LLM_MODEL_KEY: MagicMock(),
        THREAD_ID_KEY: "thread_id",
        PENDING_RESPONSE_KEY: [],
    }
    mock_logger = MagicMock()
    with patch(
        "app.assistant_v2.transaction.graph.node.call_model.extract_config",
        return_value=(config_data, MagicMock(), mock_logger),
    ), patch(
        "app.assistant_v2.transaction.graph.node.call_model.extract_tool_messages",
        return_value={},
    ) as mock_extractor, patch(
        "app.assistant_v2.transaction.graph.node.call_model.verify_ai_message",
        return_value=None,
    ) as mock_verifier, patch(
        "app.assistant_v2.transaction.graph.node.call_model._chain_ainvoke",
        AsyncMock(return_value=MagicMock()),
    ) as mock_invoker:

        result = await call_model_func(state, agent_config)

        assert TransactionAgentStateFields.MESSAGES in result
        assert len(result[TransactionAgentStateFields.MESSAGES]) == 1
        assert isinstance(result[TransactionAgentStateFields.MESSAGES][0], MagicMock)
        mock_extractor.assert_called_once_with(mock_logger, [mock_message])
        mock_verifier.assert_called_once()
        mock_invoker.assert_called_once()


def test_parse_processed_transactions():
    content = (
        '{"key": [{"account_id": "1", "amount": "100.0", "transaction_type": "Deposit",'
        ' "execution_date": "2023-01-01", "currency": "USD", "counterparty_name": "test",'
        ' "counterparty_account": "12345"}]}'
    )
    result = _parse_processed_transactions(content)
    assert "key" in result
    assert isinstance(result["key"], list)
    assert isinstance(result["key"][0], Transaction)
    assert result["key"][0].amount == 100.0
    assert result["key"][0].transaction_type == "Deposit"
    assert result["key"][0].execution_date == "2023-01-01"


def test_extract_tool_messages():
    logger = MagicMock()
    messages = [
        ToolMessage(
            name=FILTER_TRANSACTION_TOOL_NAME,
            content=(
                '{"key": [{"account_id": "1", "amount": "100.0", "transaction_type": "Deposit",'
                ' "execution_date": "2023-01-01", "currency": "USD", "counterparty_name": "test",'
                ' "counterparty_account": "12345"}]}'
            ),
            tool_call_id="1",
        )
    ]
    result = extract_tool_messages(logger, messages)
    assert TransactionAgentStateFields.PROCESSED_TRANSACTIONS in result
    assert TransactionAgentStateFields.CONFIRMED_TRANSACTIONS in result


@pytest.mark.asyncio
async def test_chain_ainvoke():
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value=MagicMock())
    input_data = {"messages": [MagicMock()]}
    await _chain_ainvoke(chain, input_data)
    chain.ainvoke.assert_called_once_with(input_data)
