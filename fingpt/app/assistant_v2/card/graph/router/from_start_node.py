from app.assistant_v2.card.graph.node import call_model_node, select_renewable_card_node
from app.assistant_v2.card.state import CardAgentState, CardAgentStateFields
from app.assistant_v2.common.base_graph import EdgeName, NodeName

call_model_edge = EdgeName("call_model")
select_renewable_card_edge = EdgeName("select_renewable_card")


start_map: dict[EdgeName, NodeName] = {
    call_model_edge: call_model_node,
    select_renewable_card_edge: select_renewable_card_node,
}


def router_from_start_node(state: CardAgentState) -> EdgeName:
    resume_node = state.get(CardAgentStateFields.RESUME_NODE, "") or ""  # type: ignore
    if resume_node:
        return list(start_map.keys())[
            list(start_map.values()).index(NodeName(resume_node))
        ]
    return call_model_edge
