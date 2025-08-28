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

select_term_deposit_account_node = NodeName("select_term_deposit_account")


@observe()
async def select_term_deposit_account_func(
    state: TermDepositAgentState, config: RunnableConfig
) -> Dict[str, Any]:
    config_data, _, logger = extract_config(config)
    logger.info(
        f"Selecting term deposit account... User choice: {config_data[USER_CHOICE_ID_KEY]}"
    )
    try:
        choice_id: str = config_data[USER_CHOICE_ID_KEY] or ""
        assert choice_id != "", "User choice is empty"
        term_deposit_accounts = state[TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS]
        term_deposit_account = term_deposit_accounts[choice_id]
        message = HumanMessage(
            f"Selected term deposit account: {term_deposit_account.name} "
            f"with deposit amount is {term_deposit_account.deposit_amount}$"
        )
        return {
            TermDepositAgentStateFields.MESSAGES: [message],
            TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS: {
                choice_id: term_deposit_account
            },
            TermDepositAgentStateFields.HUMAN_APPROVAL_TERM_DEPOSIT_ACCOUNT: True,
            TermDepositAgentStateFields.RESUME_NODE: None,
        }
    except Exception as e:
        logger.error(f"Failed to select term deposit account: {e}")
        raise
