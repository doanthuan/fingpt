from typing import Dict

from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import END_NODE, EdgeName, NodeName
from app.assistant_v2.constant import PENDING_RESPONSE_KEY
from app.assistant_v2.transfer.graph.node import call_model_node
from app.assistant_v2.transfer.state import TransferAgentState
from app.assistant_v2.util.misc import extract_config

to_model_edge = EdgeName("to_model")
to_end_edge = EdgeName("to_end")
router_map_from_review_node: Dict[EdgeName, NodeName] = {
    to_model_edge: call_model_node,
    to_end_edge: END_NODE,
}


def router_from_review(
    state: TransferAgentState,
    config: RunnableConfig,
) -> EdgeName:
    config_data, _, logger = extract_config(config)
    if not config_data.get(PENDING_RESPONSE_KEY):
        logger.debug("Expecting a response but none found. Call model again...")
        return to_model_edge
    return to_end_edge
