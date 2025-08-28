from app.assistant_v2.common.base_graph import EdgeName, NodeName
from app.assistant_v2.transaction.graph.node import (
    call_model_node,
    select_beneficiary_node,
)
from app.assistant_v2.transaction.state import (
    TransactionAgentState,
    TransactionAgentStateFields,
)

call_model_edge = EdgeName("call_model")
select_beneficiary_edge = EdgeName("select_beneficiary")

start_map: dict[EdgeName, NodeName] = {
    call_model_edge: call_model_node,
    select_beneficiary_edge: select_beneficiary_node,
}


def router_from_start_node(state: TransactionAgentState) -> EdgeName:
    resume_node = state.get(TransactionAgentStateFields.RESUME_NODE, "")  # type: ignore
    if resume_node:
        return list(start_map.keys())[
            list(start_map.values()).index(NodeName(resume_node))
        ]
    return call_model_edge
