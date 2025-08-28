import pytest
from langchain_core.messages import AIMessage, ToolCall

from app.assistant_v2.card.graph.router.from_model_node import (
    router_from_model,
    to_end_edge,
    to_review_edge,
    to_select_renewable_card_edge,
    to_tool_edge,
)
from app.assistant_v2.card.state import CardAgentStateFields
from app.entity import Card


def test_router_from_model_to_review():
    state = {
        CardAgentStateFields.MESSAGES: [AIMessage(content="test message")],
        CardAgentStateFields.RENEWABLE_CARDS: {
            "card_1": Card(
                id="card_1",
                brand="debit",
                card_type="master",
                status="Active",
                currency="USD",
                expiry_date="test_date_1",
            ),
        },
        CardAgentStateFields.HUMAN_APPROVAL_RENEWABLE_CARD: True,
    }
    assert router_from_model(state) == to_review_edge


def test_router_from_model_to_select_renewable_card():
    state = {
        CardAgentStateFields.MESSAGES: [AIMessage(content="test message")],
        CardAgentStateFields.RENEWABLE_CARDS: {
            "card_1": Card(
                id="card_1",
                brand="debit",
                card_type="master",
                status="Active",
                currency="USD",
                expiry_date="test_date_1",
            ),
        },
        CardAgentStateFields.HUMAN_APPROVAL_RENEWABLE_CARD: False,
    }
    assert router_from_model(state) == to_select_renewable_card_edge


@pytest.mark.asyncio
async def test_router_from_model_to_tool():
    state = {
        CardAgentStateFields.MESSAGES: [
            AIMessage(
                content="test message",
                tool_calls=[ToolCall(id="1", name="some_tool", args={})],
            )
        ],
    }
    assert router_from_model(state) == to_tool_edge


@pytest.mark.asyncio
async def test_router_from_model_to_end():
    state = {
        CardAgentStateFields.MESSAGES: [AIMessage(content="test message")],
        CardAgentStateFields.RENEWABLE_CARDS: {},
    }
    assert router_from_model(state) == to_end_edge
