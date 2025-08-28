from unittest.mock import patch

import pytest

from app.assistant_v2.ticker.symbol_identifier_agent import SymbolIdentifierAgent
from promptfoo.financial_report.financial_agent_runner import ticker_agent_router


@pytest.mark.asyncio
async def test_financial_agent_router():
    with patch(
        "promptfoo.financial_report.financial_agent_runner.generic_agent_router"
    ) as mock_generic_agent_router:
        mock_generic_agent_router.return_value = {"result": "test_result"}

        prompt = "Test prompt"
        options = {"option1": "value1"}
        context = {
            "vars": {"messages": ["Hello", "World"]}
        }  # Add 'vars' key with 'messages'

        result = await ticker_agent_router(prompt, options, context)

        mock_generic_agent_router.assert_called_once_with(
            prompt, options, context, SymbolIdentifierAgent.build_agent
        )
        assert result == {"result": "test_result"}
