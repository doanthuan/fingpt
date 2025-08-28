from typing import Any, Dict

from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import PENDING_RESPONSE_KEY, THREAD_ID_KEY
from app.assistant_v2.term_deposit.graph.node.select_account import select_account_node
from app.assistant_v2.term_deposit.graph.utils import _build_choices_from_accounts
from app.assistant_v2.term_deposit.state import (
    TermDepositAgentState,
    TermDepositAgentStateFields,
)
from app.assistant_v2.util.misc import extract_config
from app.entity import ChatRespAction, ChatRespDto
from app.utils.modified_langfuse_decorator import observe

multiple_active_account_match_node = NodeName("multiple_active_account_match")


@observe()
async def multiple_active_account_match_func(
    state: TermDepositAgentState,
    config: RunnableConfig,
) -> Dict[str, Any]:
    config_data, _, logger = extract_config(config)
    logger.info("Multiple matched accounts found...")
    last_message = state[TermDepositAgentStateFields.MESSAGES][-1]
    response = ChatRespDto(
        action=ChatRespAction.SHOW_CHOICES,
        thread_id=config_data[THREAD_ID_KEY],
        response=last_message.content,
        metadata=_build_choices_from_accounts(
            state[TermDepositAgentStateFields.ACTIVE_ACCOUNTS],
            state[TermDepositAgentStateFields.DEPOSIT_AMOUNT],
        ),
    )
    config_data[PENDING_RESPONSE_KEY].append(response)
    if any([c.is_enabled for c in response.metadata.choices]):
        return {
            TermDepositAgentStateFields.RESUME_NODE: select_account_node,
        }
    return {
        TermDepositAgentStateFields.MESSAGES: [],
    }
