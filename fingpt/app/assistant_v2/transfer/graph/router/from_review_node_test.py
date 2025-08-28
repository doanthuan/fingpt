from app.assistant_v2.constant import PENDING_RESPONSE_KEY
from app.assistant_v2.transfer.graph.router.from_review_node import (
    router_from_review,
    to_end_edge,
    to_model_edge,
)
from app.assistant_v2.transfer.state import TransferAgentState
from app.assistant_v2.util.misc import extract_config


def test_router_from_review_with_response(agent_config):
    state = TransferAgentState()
    config, ctx, logger = extract_config(agent_config)
    config[PENDING_RESPONSE_KEY] = ["response"]
    assert router_from_review(state, agent_config) == to_end_edge


def test_router_form_review_no_response(agent_config):
    state = TransferAgentState()
    config, ctx, logger = extract_config(agent_config)
    config[PENDING_RESPONSE_KEY] = []
    assert router_from_review(state, agent_config) == to_model_edge
