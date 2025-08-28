from typing import Any, Dict

from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import USER_CHOICE_ID_KEY
from app.assistant_v2.term_deposit.state import (
    TermDepositAgentState,
    TermDepositAgentStateFields,
)
from app.assistant_v2.util.misc import extract_config
from app.utils.modified_langfuse_decorator import observe

select_account_node = NodeName("select_account")


@observe()
async def select_account_func(
    state: TermDepositAgentState, config: RunnableConfig
) -> Dict[str, Any]:
    config_data, _, logger = extract_config(config)
    logger.info(f"Selecting account... User choice: {config_data[USER_CHOICE_ID_KEY]}")
    try:
        choice_id: str = config_data[USER_CHOICE_ID_KEY] or ""
        assert choice_id != "", "User choice is empty"
        accounts = state[TermDepositAgentStateFields.ACTIVE_ACCOUNTS]
        account = accounts[choice_id]
        message = HumanMessage(f"Selected account: {account.name}")
        return {
            TermDepositAgentStateFields.MESSAGES: [message],
            TermDepositAgentStateFields.ACTIVE_ACCOUNTS: {choice_id: account},
            TermDepositAgentStateFields.HUMAN_APPROVAL_ACTIVE_ACCOUNT: True,
            TermDepositAgentStateFields.RESUME_NODE: None,
        }
    except Exception as e:
        logger.error(f"Failed to select account: {e}")
        raise
