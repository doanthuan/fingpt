from typing import Dict

from app.assistant_v2.common.base_graph import END_NODE, EdgeName, NodeName
from app.assistant_v2.transaction.graph.node import (
    generate_chart_data_node,
    multiple_beneficiary_match_node,
)
from app.assistant_v2.transaction.graph.tool import tool_node
from app.assistant_v2.transaction.state import (
    TransactionAgentState,
    TransactionAgentStateFields,
)

to_generate_chart_node = EdgeName("to_generate_chart")
to_select_beneficiary_node = EdgeName("to_select_beneficiary")
to_tool_edge = EdgeName("to_tool")
to_end_edge = EdgeName("to_end")

router_map_from_model: Dict[EdgeName, NodeName] = {
    to_generate_chart_node: generate_chart_data_node,
    to_select_beneficiary_node: multiple_beneficiary_match_node,
    to_tool_edge: tool_node,
    to_end_edge: END_NODE,
}


def router_from_model(state: TransactionAgentState) -> EdgeName:
    last_message = state[TransactionAgentStateFields.MESSAGES][-1]
    confirmed_transaction = state.get(
        TransactionAgentStateFields.CONFIRMED_TRANSACTIONS
    )
    processed_transactions = state.get(
        TransactionAgentStateFields.PROCESSED_TRANSACTIONS
    )

    if not last_message.tool_calls:
        if confirmed_transaction:
            return to_generate_chart_node
        elif processed_transactions:
            return to_select_beneficiary_node
        else:
            return to_end_edge
    else:
        return to_tool_edge
