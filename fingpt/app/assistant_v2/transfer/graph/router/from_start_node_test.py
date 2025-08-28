import pytest

from app.assistant_v2.transfer.graph.node.select_account import select_account_node
from app.assistant_v2.transfer.graph.router.from_start_node import (
    call_model_edge,
    router_from_start_node,
    select_account_edge,
)
from app.assistant_v2.transfer.state import TransferAgentStateFields


def test_router_from_start_node_with_resume_node():
    state = {TransferAgentStateFields.RESUME_NODE: select_account_node}
    assert router_from_start_node(state) == select_account_edge


def test_router_from_start_node_without_resume_node():
    state = {TransferAgentStateFields.RESUME_NODE: ""}
    assert router_from_start_node(state) == call_model_edge


def test_router_from_start_node_with_invalid_resume_node():
    state = {TransferAgentStateFields.RESUME_NODE: "invalid_node"}
    with pytest.raises(ValueError):
        router_from_start_node(state)
