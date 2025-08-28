from unittest.mock import patch

import pytest

from app.assistant_v2.card.graph.node import call_model_func
from app.assistant_v2.card.state import CardAgentState
from app.assistant_v2.primary.card_controller import CardController
from promptfoo.card.card_agent_runner import call_api, card_agent_router


@pytest.mark.asyncio
async def test_call_api():
    with patch(
        "promptfoo.card.card_agent_runner.common_call_api"
    ) as mock_common_call_api:
        mock_common_call_api.return_value = {"result": "test_result"}

        prompt = "Test prompt"
        options = {"option1": "value1"}
        context = {"context1": "value1"}

        result = await call_api(prompt, options, context)

        mock_common_call_api.assert_called_once_with(
            prompt, options, context, CardAgentState, call_model_func
        )
        assert result == {"result": "test_result"}


@pytest.mark.asyncio
async def test_term_deposit_agent_router():
    with patch(
        "promptfoo.card.card_agent_runner.generic_agent_router"
    ) as mock_generic_agent_router:
        mock_generic_agent_router.return_value = {"result": "test_result"}

        prompt = "Test prompt"
        options = {"option1": "value1"}
        context = {"context1": "value1"}

        result = await card_agent_router(prompt, options, context)

        mock_generic_agent_router.assert_called_once_with(
            prompt, options, context, CardController.build_agent
        )
        assert result == {"result": "test_result"}
