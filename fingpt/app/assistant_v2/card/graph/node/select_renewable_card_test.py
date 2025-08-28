import pytest

from app.assistant_v2.card.graph.node.select_renewable_card import (
    select_renewable_card_func,
)
from app.assistant_v2.card.state import CardAgentStateFields
from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, USER_CHOICE_ID_KEY
from app.entity import Card


@pytest.mark.asyncio
async def test_select_renewable_card(agent_config):
    # Mock the state and config
    state = {
        CardAgentStateFields.RENEWABLE_CARDS: {
            "card_1": Card(
                id="card_1",
                brand="test_brand",
                card_type="test_card_type",
                status="test_status",
                currency="USD",
                expiry_date="test_date",
            ),
            "card_2": Card(
                id="card_2",
                brand="test_brand",
                card_type="test_card_type",
                status="test_status",
                currency="USD",
                expiry_date="test_date",
            ),
        }
    }
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})
    config_data[USER_CHOICE_ID_KEY] = "card_1"

    # Call the function
    output = await select_renewable_card_func(state, agent_config)

    # Assertions
    assert CardAgentStateFields.MESSAGES in output
    assert (
        output[CardAgentStateFields.MESSAGES][0].content
        == "Selected renewable card id: card_1"
    )
    assert CardAgentStateFields.RENEWABLE_CARDS in output
    assert list(output[CardAgentStateFields.RENEWABLE_CARDS].values())[0].id == "card_1"
    assert CardAgentStateFields.RESUME_NODE in output
    assert output[CardAgentStateFields.RESUME_NODE] is None


@pytest.mark.asyncio
async def test_select_renewable_card_no_choice(agent_config):
    # Mock the state and config
    state = {
        CardAgentStateFields.RENEWABLE_CARDS: {
            "card_1": Card(
                id="card_1",
                brand="test_brand",
                card_type="test_card_type",
                status="test_status",
                currency="USD",
                expiry_date="test_date",
            ),
        }
    }
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})
    config_data[USER_CHOICE_ID_KEY] = ""

    # Call the function and expect an assertion error
    with pytest.raises(AssertionError, match="User choice is empty"):
        await select_renewable_card_func(state, agent_config)
