from typing import Any, Dict

from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import USER_CHOICE_ID_KEY
from app.assistant_v2.transfer.state import TransferAgentState, TransferAgentStateFields
from app.assistant_v2.util.misc import extract_config
from app.utils.modified_langfuse_decorator import observe

select_account_node = NodeName("select_account")


@observe()
async def select_account_func(
    state: TransferAgentState, config: RunnableConfig
) -> Dict[str, Any]:
    config_data, _, logger = extract_config(config)
    logger.info(f"Selecting account... User choice: {config_data[USER_CHOICE_ID_KEY]}")
    try:
        choice_id: str = config_data[USER_CHOICE_ID_KEY] or ""
        assert choice_id != "", "User choice is empty"
        accounts = state[TransferAgentStateFields.ACTIVE_ACCOUNTS]
        account = next(
            (account for account in accounts if account.id == choice_id), None
        )
        return {
            TransferAgentStateFields.MESSAGES: [
                HumanMessage(
                    content=f"My select account is id: {account.id}, name: {account.name}"
                )
            ],
            TransferAgentStateFields.ACTIVE_ACCOUNTS: [],
            TransferAgentStateFields.SELECTED_ACCOUNT: account,
            TransferAgentStateFields.RESUME_NODE: None,
        }
    except Exception as e:
        logger.error(f"Failed to select account: {e}")
        raise
