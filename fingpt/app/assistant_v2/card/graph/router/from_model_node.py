from typing import Dict

from app.assistant_v2.card.graph.node.available_renewable_card import (
    available_renewable_card_node,
)
from app.assistant_v2.card.graph.node.review_card import review_card_node
from app.assistant_v2.card.graph.tool import tool_node
from app.assistant_v2.card.state import CardAgentState, CardAgentStateFields
from app.assistant_v2.common.base_graph import END_NODE, EdgeName, NodeName

to_review_edge = EdgeName("to_review")
to_select_renewable_card_edge = EdgeName("to_select_renewable_card")
to_tool_edge = EdgeName("to_tool")
to_end_edge = EdgeName("to_end")

router_map_from_model: Dict[EdgeName, NodeName] = {
    to_review_edge: review_card_node,
    to_select_renewable_card_edge: available_renewable_card_node,
    to_tool_edge: tool_node,
    to_end_edge: END_NODE,
}


def _router_to_hil(state: CardAgentState) -> EdgeName:
    renewable_cards = state.get(CardAgentStateFields.RENEWABLE_CARDS, {})
    human_approval_renewable_card = state.get(
        CardAgentStateFields.HUMAN_APPROVAL_RENEWABLE_CARD, False
    )

    print(f"Renewable cards {renewable_cards}")
    print(f"Human approval renewable card: {human_approval_renewable_card}")

    if len(renewable_cards) == 1 and human_approval_renewable_card:
        print("Next node: review")
        return to_review_edge

    if renewable_cards and not human_approval_renewable_card:
        print("Next node: select renewable card")
        return to_select_renewable_card_edge

    print("Next node: end")
    return to_end_edge


def router_from_model(state: CardAgentState) -> EdgeName:
    last_message = state[CardAgentStateFields.MESSAGES][-1]
    if not last_message.tool_calls:
        return _router_to_hil(state)
    else:
        return to_tool_edge
