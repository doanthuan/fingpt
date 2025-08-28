from app.assistant_v2.common.base_graph import EdgeName, NodeName
from app.assistant_v2.transfer.graph.node import (
    call_model_node,
    select_account_node,
    select_contact_node,
)
from app.assistant_v2.transfer.state import TransferAgentState, TransferAgentStateFields

call_model_edge = EdgeName("call_model")
select_account_edge = EdgeName("select_account")
select_contact_edge = EdgeName("select_contact")

start_map: dict[EdgeName, NodeName] = {
    call_model_edge: call_model_node,
    select_account_edge: select_account_node,
    select_contact_edge: select_contact_node,
}


def router_from_start_node(state: TransferAgentState) -> EdgeName:
    resume_node = state.get(TransferAgentStateFields.RESUME_NODE, "") or ""  # type: ignore
    if resume_node:
        return list(start_map.keys())[
            list(start_map.values()).index(NodeName(resume_node))
        ]
    return call_model_edge
