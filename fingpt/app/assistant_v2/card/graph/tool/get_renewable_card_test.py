import json
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.assistant_v2.card.graph.tool.get_renewable_card import _get_renewable_card
from app.entity import Card


@pytest.mark.asyncio
async def test_get_renewable_card_success(agent_config):
    # Mock the list_cards function
    cards = [
        Card(
            id="card_1",
            brand="debit",
            card_type="master",
            status="Active",
            currency="USD",
            expiry_date=(date.today() + timedelta(days=40)).strftime("%Y-%m-%d"),
        ),
        Card(
            id="card_2",
            brand="debit",
            card_type="master",
            status="NonActive",
            currency="USD",
            expiry_date=(date.today() + timedelta(days=20)).strftime("%Y-%m-%d"),
        ),
    ]
    mock_cards = AsyncMock(return_value=cards)
    with patch(
        "app.assistant_v2.card.graph.tool.get_renewable_card.list_cards",
        mock_cards,
    ):
        result = await _get_renewable_card(agent_config, expired_days=30)

        # Assertions
        result_list = eval(result)
        result_cards = [Card(**json.loads(card)) for card in result_list]
        assert result_cards == [cards[1]]


@pytest.mark.asyncio
async def test_get_renewable_card_failure(agent_config):
    # Mock the list_cards function to raise an exception
    with patch(
        "app.assistant_v2.card.graph.tool.get_renewable_card.list_cards",
        side_effect=Exception("API error"),
    ):
        # Call the function and expect an exception
        with pytest.raises(Exception, match="API error"):
            await _get_renewable_card(agent_config, expired_days=30)
