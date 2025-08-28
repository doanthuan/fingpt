import asyncio

from app.assistant_v2.common.base_graph import BaseGraph
from app.assistant_v2.transaction.graph.node import (
    call_model_func,
    call_model_node,
    generate_chart_data_func,
    generate_chart_data_node,
    multiple_beneficiary_match_func,
    multiple_beneficiary_match_node,
    select_beneficiary_func,
    select_beneficiary_node,
)
from app.assistant_v2.transaction.graph.router import (
    router_from_model,
    router_map_from_model,
)
from app.assistant_v2.transaction.graph.router.from_start_node import (
    router_from_start_node,
    start_map,
)
from app.assistant_v2.transaction.graph.tool import tool_node, tool_node_executable
from app.assistant_v2.transaction.state import (
    TransactionAgentConfig,
    TransactionAgentState,
)


class TransactionGraph(BaseGraph[TransactionAgentState]):
    def __init__(self):
        super().__init__(TransactionAgentState, TransactionAgentConfig)

    async def initialize(self) -> None:
        # Nodes:
        self.add_node(call_model_node, call_model_func)
        self.add_node(tool_node, tool_node_executable)
        self.add_node(multiple_beneficiary_match_node, multiple_beneficiary_match_func)
        self.add_node(select_beneficiary_node, select_beneficiary_func)
        self.add_node(generate_chart_data_node, generate_chart_data_func)

        # Edges:
        # From start
        self.add_start_router(router_from_start_node, start_map)
        # To model
        self.add_edge(select_beneficiary_node, call_model_node)
        # From model
        self.add_conditional_edges(
            start=call_model_node,
            router=router_from_model,
            path_map=router_map_from_model,
        )
        # To tools and back
        self.add_edge(tool_node, call_model_node)
        # To end
        self.route_to_end(generate_chart_data_node)
        self.route_to_end(multiple_beneficiary_match_node)


if __name__ == "__main__":
    transaction_graph = asyncio.run(TransactionGraph().get_graph())
    transaction_graph.draw_mermaid_png(output_file_path="transaction_graph.png")
