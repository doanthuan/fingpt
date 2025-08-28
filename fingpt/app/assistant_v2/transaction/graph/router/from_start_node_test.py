import pytest

from app.assistant_v2.transaction.graph.node import select_beneficiary_node
from app.assistant_v2.transaction.graph.router.from_start_node import (
    call_model_edge,
    router_from_start_node,
    select_beneficiary_edge,
)
from app.assistant_v2.transaction.state import TransactionAgentStateFields


def test_router_from_start_node_with_resume_node():
    state = {TransactionAgentStateFields.RESUME_NODE: select_beneficiary_node}
    result = router_from_start_node(state)
    assert result == select_beneficiary_edge


def test_router_from_start_node_without_resume_node():
    state = {TransactionAgentStateFields.RESUME_NODE: ""}
    result = router_from_start_node(state)
    assert result == call_model_edge


def test_router_from_start_node_with_invalid_resume_node():
    state = {TransactionAgentStateFields.RESUME_NODE: "invalid_node"}
    with pytest.raises(ValueError, match="'invalid_node' is not in list"):
        router_from_start_node(state)
