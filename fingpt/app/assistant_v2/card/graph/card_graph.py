from app.assistant_v2.card.config import CardAgentConfig
from app.assistant_v2.card.graph.node import (
    available_renewable_card_func,
    available_renewable_card_node,
    call_model_func,
    call_model_node,
    review_card_func,
    review_card_node,
    select_renewable_card_func,
    select_renewable_card_node,
)
from app.assistant_v2.card.graph.router import (
    router_from_model,
    router_from_start_node,
    router_map_from_model,
    start_map,
)
from app.assistant_v2.card.graph.tool import tool_node, tool_node_executable
from app.assistant_v2.card.state import CardAgentState
from app.assistant_v2.common.base_graph import BaseGraph


class CardGraph(BaseGraph[CardAgentState]):
    def __init__(self):
        super().__init__(CardAgentState, CardAgentConfig)

    async def initialize(self) -> None:
        # Nodes:
        self.add_node(call_model_node, call_model_func)
        self.add_node(tool_node, tool_node_executable)
        self.add_node(available_renewable_card_node, available_renewable_card_func)
        self.add_node(select_renewable_card_node, select_renewable_card_func)
        self.add_node(review_card_node, review_card_func)

        # Edges:
        # From start
        self.add_start_router(router_from_start_node, start_map)
        # To model
        self.add_edge(select_renewable_card_node, call_model_node)
        # From model
        self.add_conditional_edges(
            start=call_model_node,
            router=router_from_model,
            path_map=router_map_from_model,
        )
        # To tools and back
        self.add_edge(tool_node, call_model_node)
        # To end
        self.route_to_end(review_card_node)
        self.route_to_end(available_renewable_card_node)
