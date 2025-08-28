from unittest.mock import patch

import pytest

from app.assistant_v2.transfer.graph.node import call_model_func
from app.assistant_v2.transfer.money_transfer_agent import MoneyTransferAgent
from app.assistant_v2.transfer.state import TransferAgentState
from promptfoo.transfer.transfer_agent_runner import call_api, transfer_agent_router


@pytest.mark.asyncio
async def test_call_api():
    with patch(
        "promptfoo.transfer.transfer_agent_runner.common_call_api"
    ) as mock_common_call_api:
        mock_common_call_api.return_value = {"result": "test_result"}

        prompt = "Test prompt"
        options = {"option1": "value1"}
        context = {"context1": "value1"}

        result = await call_api(prompt, options, context)

        mock_common_call_api.assert_called_once_with(
            prompt, options, context, TransferAgentState, call_model_func
        )
        assert result == {"result": "test_result"}


@pytest.mark.asyncio
async def test_transfer_agent_router():
    with patch(
        "promptfoo.transfer.transfer_agent_runner.generic_agent_router"
    ) as mock_generic_agent_router:
        mock_generic_agent_router.return_value = {"result": "test_result"}

        prompt = "Test prompt"
        options = {"option1": "value1"}
        context = {"context1": "value1"}

        result = await transfer_agent_router(prompt, options, context)

        mock_generic_agent_router.assert_called_once_with(
            prompt, options, context, MoneyTransferAgent.build_agent
        )
        assert result == {"result": "test_result"}
