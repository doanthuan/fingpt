from typing import Any

from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import BaseGraph
from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    USER_CHOICE_ID_KEY,
)
from app.assistant_v2.transfer.graph.node import (
    call_model_func,
    call_model_node,
    multiple_active_account_match_func,
    multiple_active_account_match_node,
    multiple_contact_match_func,
    multiple_contact_match_node,
    review_transfer_func,
    review_transfer_node,
    select_account_func,
    select_account_node,
    select_contact_func,
    select_contact_node,
)
from app.assistant_v2.transfer.graph.router import (
    router_from_model,
    router_from_review,
    router_from_start_node,
    router_map_from_model,
    router_map_from_review_node,
    start_map,
)
from app.assistant_v2.transfer.graph.tool import tool_node, tool_node_executable
from app.assistant_v2.transfer.state import (
    TransferAgentConfig,
    TransferAgentState,
    TransferAgentStateFields,
)
from app.core import RequestContext


class TransferGraph(BaseGraph[TransferAgentState]):
    def __init__(self):
        super().__init__(TransferAgentState, TransferAgentConfig)

    @staticmethod
    def clear_state_except_messages(state: TransferAgentState) -> dict[str, Any]:
        ignore_field = {
            TransferAgentStateFields.MESSAGES,
            TransferAgentStateFields.TRANSFER_AMOUNT,
            TransferAgentStateFields.ACTIVE_ACCOUNTS,
            TransferAgentStateFields.CONTACT_LIST,
            TransferAgentStateFields.SELECTED_ACCOUNT,
            TransferAgentStateFields.SELECTED_CONTACT,
        }
        for k, v in state.items():
            if k in ignore_field:
                continue
            elif isinstance(v, list):
                state[k] = []
            elif isinstance(v, dict):
                state[k] = {}
            else:
                state[k] = None
        return state

    @staticmethod
    async def start_node_fnc(
        state: TransferAgentState, config: RunnableConfig
    ) -> dict[str, Any]:
        """
        Check the state and config before running into the user-defined graph.
        Args:
            state:
            config:

        Returns: the verified state and config
        """
        config_data = config.get(CONFIGURABLE_CONTEXT_KEY, {})
        ctx: RequestContext = config_data.get(CONTEXT_KEY)
        logger = ctx.logger()
        resume_node = state.get(TransferAgentStateFields.RESUME_NODE)
        user_choice_id = config.get(CONFIGURABLE_CONTEXT_KEY, {}).get(
            USER_CHOICE_ID_KEY
        )
        if resume_node and not user_choice_id:
            logger.warn(
                f"Request to resume at node {resume_node} but no user choice id, "
                f"clear current state except messages"
            )
            return TransferGraph.clear_state_except_messages(state)
        if not resume_node and user_choice_id:
            logger.warn(
                f"Request to resume with user choice id {user_choice_id} but no resume node, clear user choice id"
            )
            config_data[USER_CHOICE_ID_KEY] = None
        return {TransferAgentStateFields.MESSAGES: []}  # nothing to update

    async def initialize(self) -> None:
        # Nodes:
        self.add_node(call_model_node, call_model_func)
        self.add_node(tool_node, tool_node_executable)
        self.add_node(multiple_contact_match_node, multiple_contact_match_func)
        self.add_node(select_contact_node, select_contact_func)
        self.add_node(
            multiple_active_account_match_node, multiple_active_account_match_func
        )
        self.add_node(select_account_node, select_account_func)
        self.add_node(review_transfer_node, review_transfer_func)

        # Edges:
        # From start
        self.add_start_router(router_from_start_node, start_map)
        # To model
        self.add_edge(select_account_node, call_model_node)
        self.add_edge(select_contact_node, call_model_node)
        # From model
        self.add_conditional_edges(
            start=call_model_node,
            router=router_from_model,
            path_map=router_map_from_model,
        )
        # To tools and back
        self.add_edge(tool_node, call_model_node)
        # To end
        self.add_conditional_edges(
            start=review_transfer_node,
            router=router_from_review,
            path_map=router_map_from_review_node,
        )
        self.route_to_end(review_transfer_node)
        self.route_to_end(multiple_contact_match_node)
        self.route_to_end(multiple_active_account_match_node)
