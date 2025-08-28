import pytest
from langchain_core.messages import HumanMessage

from app.assistant_v2.card.graph.node.review_card import review_card_func
from app.assistant_v2.card.state import CardAgentStateFields
from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, PENDING_RESPONSE_KEY
from app.entity import Card, ChatRespAction


@pytest.mark.asyncio
async def test_review_card(agent_config):
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
            )
        },
        CardAgentStateFields.MESSAGES: [HumanMessage(content="test message")],
    }

    # Call the function
    output = await review_card_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})

    # Assertions
    assert CardAgentStateFields.MESSAGES in output
    assert output[CardAgentStateFields.MESSAGES][0].content == "It's okay."
    assert CardAgentStateFields.RESUME_NODE in output
    assert output[CardAgentStateFields.RESUME_NODE] is None
    assert output[CardAgentStateFields.RENEWABLE_CARDS] == {}
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert config_data[PENDING_RESPONSE_KEY][0].action == ChatRespAction.RENEW_CARD
