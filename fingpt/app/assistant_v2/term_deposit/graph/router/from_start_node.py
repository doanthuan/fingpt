from app.assistant_v2.common.base_graph import EdgeName, NodeName
from app.assistant_v2.term_deposit.graph.node import (
    call_model_node,
    present_offer_node,
    select_account_node,
    select_term_deposit_account_node,
    select_term_deposit_product_node,
)
from app.assistant_v2.term_deposit.state import (
    TermDepositAgentState,
    TermDepositAgentStateFields,
)

call_model_edge = EdgeName("call_model")
select_account_edge = EdgeName("select_account")
select_term_deposit_account_edge = EdgeName("select_term_deposit_account")
select_term_deposit_product_edge = EdgeName("select_term_deposit_product")
present_offer_edge = EdgeName("present_offer")

start_map: dict[EdgeName, NodeName] = {
    call_model_edge: call_model_node,
    select_account_edge: select_account_node,
    select_term_deposit_account_edge: select_term_deposit_account_node,
    select_term_deposit_product_edge: select_term_deposit_product_node,
    present_offer_edge: present_offer_node,
}


def router_from_start_node(state: TermDepositAgentState) -> EdgeName:
    resume_node = state.get(TermDepositAgentStateFields.RESUME_NODE, "") or ""  # type: ignore
    if resume_node:
        return list(start_map.keys())[
            list(start_map.values()).index(NodeName(resume_node))
        ]
    return call_model_edge
