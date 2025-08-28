from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.assistant_v2.card.constant import (
    GET_CARD_TOOL_NAME,
    GET_RENEWABLE_CARD_TOOL_NAME,
)
from app.assistant_v2.card.graph.node.call_model import call_model_func
from app.assistant_v2.card.state import CardAgentStateFields
from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, PENDING_RESPONSE_KEY
from app.entity import Card


@pytest.mark.asyncio
async def test_call_model(agent_config):
    get_card_message = ToolMessage(
        name=GET_CARD_TOOL_NAME,
        content=str(
            [
                Card(
                    id="card_1",
                    brand="debit",
                    card_type="master",
                    status="Active",
                    currency="USD",
                    expiry_date="test_date_1",
                ).json()
            ]
        ),
        tool_call_id="1",
    )
    get_renewable_card_message = ToolMessage(
        name=GET_RENEWABLE_CARD_TOOL_NAME,
        content=str(
            [
                Card(
                    id="card_2",
                    brand="debit",
                    card_type="master",
                    status="Active",
                    currency="USD",
                    expiry_date="test_date_2",
                ).json()
            ]
        ),
        tool_call_id="2",
    )

    human_message = HumanMessage(content="test message")
    messages = [
        human_message,
        get_card_message,
        get_renewable_card_message,
    ]
    # Mock the state and config
    state = {CardAgentStateFields.MESSAGES: messages}

    mock_chain_ainvoke = patch(
        "app.assistant_v2.card.graph.node.call_model.chain_ainvoke",
        AsyncMock(return_value=AIMessage(content="response content")),
    ).start()

    # Call the function
    output = await call_model_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})
    print(output)
    # Assertions
    assert CardAgentStateFields.MESSAGES in output
    assert output[CardAgentStateFields.MESSAGES][0].content == "response content"
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert config_data[PENDING_RESPONSE_KEY][0].response == "response content"
    assert list(output[CardAgentStateFields.RENEWABLE_CARDS].values())[0].id == "card_2"
    # Stop patches
    mock_chain_ainvoke.stop()
