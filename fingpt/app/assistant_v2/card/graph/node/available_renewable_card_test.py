import pytest
from langchain_core.messages import HumanMessage

from app.assistant_v2.card.graph.node.available_renewable_card import (
    available_renewable_card_func,
)
from app.assistant_v2.card.graph.node.select_renewable_card import (
    select_renewable_card_node,
)
from app.assistant_v2.card.state import CardAgentStateFields
from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, PENDING_RESPONSE_KEY
from app.entity import Card


@pytest.mark.asyncio
async def test_available_term_deposit_account(agent_config):
    # Mock the state and config
    state = {
        CardAgentStateFields.MESSAGES: [HumanMessage(content="test message")],
        CardAgentStateFields.RENEWABLE_CARDS: {
            "card_1": Card(
                id="card_1",
                brand="debit",
                card_type="master",
                status="Active",
                currency="USD",
                expiry_date="test_date_1",
            ),
            "card_2": Card(
                id="card_2",
                brand="debit",
                card_type="master",
                status="NonActive",
                currency="USD",
                expiry_date="test_date_2",
            ),
        },
    }

    # Call the function
    output = await available_renewable_card_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})

    # Assertions
    assert CardAgentStateFields.RESUME_NODE in output
    assert output[CardAgentStateFields.RESUME_NODE] == select_renewable_card_node
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert config_data[PENDING_RESPONSE_KEY][0].action == "SHOW_CHOICES"
    assert len(config_data[PENDING_RESPONSE_KEY][0].metadata.choices) == 2
