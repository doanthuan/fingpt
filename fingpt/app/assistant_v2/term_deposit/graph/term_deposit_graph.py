from typing import Any

from langchain_core.runnables import RunnableConfig

from app.assistant_v2.common.base_graph import BaseGraph
from app.assistant_v2.term_deposit.config import TermDepositAgentConfig
from app.assistant_v2.term_deposit.graph.node import (
    available_term_deposit_account_func,
    available_term_deposit_account_node,
    available_term_deposit_product_func,
    available_term_deposit_product_node,
    call_model_func,
    call_model_node,
    multiple_active_account_match_func,
    multiple_active_account_match_node,
    present_offer_func,
    present_offer_node,
    review_term_deposit_func,
    review_term_deposit_node,
    select_account_func,
    select_account_node,
    select_term_deposit_account_func,
    select_term_deposit_account_node,
    select_term_deposit_product_func,
    select_term_deposit_product_node,
)
from app.assistant_v2.term_deposit.graph.router import (
    router_from_model,
    router_from_start_node,
    router_map_from_model,
    start_map,
)
from app.assistant_v2.term_deposit.graph.tool import tool_node, tool_node_executable
from app.assistant_v2.term_deposit.state import (
    TermDepositAgentState,
    TermDepositAgentStateFields,
)


class TermDepositGraph(BaseGraph[TermDepositAgentState]):
    def __init__(self):
        super().__init__(TermDepositAgentState, TermDepositAgentConfig)

    @staticmethod
    async def start_node_fnc(
        state: TermDepositAgentState, config: RunnableConfig
    ) -> dict[str, Any]:
        """
        Custom start node function for TermDepositGraph.
        """
        action = state.get(TermDepositAgentStateFields.ACTION, None)
        print(f"action: {action}")
        if action == "get_offer":
            return {
                TermDepositAgentStateFields.MESSAGES: []
            }  # Continue without clearing state
        return await BaseGraph.start_node_fnc(state, config)

    async def initialize(self) -> None:
        # Nodes:
        self.add_node(call_model_node, call_model_func)
        self.add_node(tool_node, tool_node_executable)
        self.add_node(
            available_term_deposit_account_node, available_term_deposit_account_func
        )
        self.add_node(
            select_term_deposit_account_node, select_term_deposit_account_func
        )
        self.add_node(
            multiple_active_account_match_node, multiple_active_account_match_func
        )
        self.add_node(select_account_node, select_account_func)
        self.add_node(
            available_term_deposit_product_node, available_term_deposit_product_func
        )
        self.add_node(
            select_term_deposit_product_node, select_term_deposit_product_func
        )
        self.add_node(review_term_deposit_node, review_term_deposit_func)
        self.add_node(present_offer_node, present_offer_func)

        # Edges:
        # From start
        self.add_start_router(router_from_start_node, start_map)
        # To model
        self.add_edge(select_account_node, call_model_node)
        self.add_edge(select_term_deposit_account_node, call_model_node)
        self.add_edge(select_term_deposit_product_node, call_model_node)
        # From model
        self.add_conditional_edges(
            start=call_model_node,
            router=router_from_model,
            path_map=router_map_from_model,
        )
        # To tools and back
        self.add_edge(tool_node, call_model_node)
        # To end
        self.route_to_end(review_term_deposit_node)
        self.route_to_end(available_term_deposit_account_node)
        self.route_to_end(multiple_active_account_match_node)
        self.route_to_end(available_term_deposit_product_node)
        self.route_to_end(present_offer_node)
