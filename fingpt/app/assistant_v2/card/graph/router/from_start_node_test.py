import pytest

from app.assistant_v2.card.graph.node.select_renewable_card import (
    select_renewable_card_node,
)
from app.assistant_v2.card.graph.router.from_start_node import (
    call_model_edge,
    router_from_start_node,
    select_renewable_card_edge,
)
from app.assistant_v2.card.state import CardAgentStateFields


def test_router_from_start_node_with_resume_node():
    state = {CardAgentStateFields.RESUME_NODE: select_renewable_card_node}
    assert router_from_start_node(state) == select_renewable_card_edge


def test_router_from_start_node_without_resume_node():
    state = {CardAgentStateFields.RESUME_NODE: ""}
    assert router_from_start_node(state) == call_model_edge


def test_router_from_start_node_with_invalid_resume_node():
    state = {CardAgentStateFields.RESUME_NODE: "invalid_node"}
    with pytest.raises(ValueError):
        router_from_start_node(state)
