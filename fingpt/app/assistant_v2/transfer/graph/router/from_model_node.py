from typing import Dict

from app.assistant_v2.common.base_graph import END_NODE, EdgeName, NodeName
from app.assistant_v2.transfer.graph.node.multiple_active_account_match import (
    multiple_active_account_match_node,
)
from app.assistant_v2.transfer.graph.node.multiple_contact_match import (
    multiple_contact_match_node,
)
from app.assistant_v2.transfer.graph.node.review_transfer import review_transfer_node
from app.assistant_v2.transfer.graph.tool import tool_node
from app.assistant_v2.transfer.state import TransferAgentState, TransferAgentStateFields

to_review_edge = EdgeName("to_review")
to_select_account_edge = EdgeName("to_select_account")
to_select_contact_edge = EdgeName("to_select_contact")
to_tool_edge = EdgeName("to_tool")
to_end_edge = EdgeName("to_end")

router_map_from_model: Dict[EdgeName, NodeName] = {
    to_review_edge: review_transfer_node,
    to_select_contact_edge: multiple_contact_match_node,
    to_select_account_edge: multiple_active_account_match_node,
    to_tool_edge: tool_node,
    to_end_edge: END_NODE,
}


def _router_to_hil(state: TransferAgentState) -> EdgeName:
    contacts = state.get(TransferAgentStateFields.CONTACT_LIST, [])
    accounts = state.get(TransferAgentStateFields.ACTIVE_ACCOUNTS, [])
    selected_contact = state.get(TransferAgentStateFields.SELECTED_CONTACT)
    selected_account = state.get(TransferAgentStateFields.SELECTED_ACCOUNT)

    if selected_contact and selected_account:
        return to_review_edge
    if len(contacts) > 1:
        return to_select_contact_edge
    if len(accounts) > 1:
        return to_select_account_edge
    return to_end_edge


def router_from_model(state: TransferAgentState) -> EdgeName:
    last_message = state[TransferAgentStateFields.MESSAGES][-1]
    if not last_message.tool_calls:
        return _router_to_hil(state)
    else:
        return to_tool_edge
