import json
from unittest.mock import AsyncMock, patch

import pytest

from app.assistant_v2.card.graph.tool.get_card import _get_card
from app.entity import Card


@pytest.mark.asyncio
async def test_get_card_success(agent_config):
    # Mock the list_cards function
    cards = [
        Card(
            id="card_1",
            brand="debit",
            card_type="master",
            status="Active",
            currency="USD",
            expiry_date="test_date_1",
        ),
        Card(
            id="card_2",
            brand="debit",
            card_type="master",
            status="NonActive",
            currency="USD",
            expiry_date="test_date_2",
        ),
    ]
    mock_cards = AsyncMock(return_value=cards)
    with patch(
        "app.assistant_v2.card.graph.tool.get_card.list_cards",
        mock_cards,
    ):
        result = await _get_card(agent_config)

        # Assertions
        result_list = eval(result)
        result_cards = [Card(**json.loads(card)) for card in result_list]
        assert result_cards == cards


@pytest.mark.asyncio
async def test_get_card_failure(agent_config):
    # Mock the list_cards function to raise an exception
    with patch(
        "app.assistant_v2.card.graph.tool.get_card.list_cards",
        side_effect=Exception("API error"),
    ):
        # Call the function and expect an exception
        with pytest.raises(Exception, match="API error"):
            await _get_card(agent_config)
