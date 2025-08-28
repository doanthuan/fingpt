from typing import Any, Dict

from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import USER_CHOICE_ID_KEY
from app.assistant_v2.transaction.state import (
    TransactionAgentState,
    TransactionAgentStateFields,
)
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.assistant_v2.util.misc import extract_config
from app.utils.modified_langfuse_decorator import observe

select_beneficiary_node = NodeName("select_beneficiary")


@observe()
async def select_beneficiary_func(
    state: TransactionAgentState, config: RunnableConfig
) -> Dict[str, Any]:
    config_data, _, logger = extract_config(config)
    logger.info(
        f"Selecting accoung beneficiary... User choice: {config_data[USER_CHOICE_ID_KEY]}"
    )
    try:
        choice_id: str = config_data[USER_CHOICE_ID_KEY] or ""
        assert choice_id != "", "User choice is empty"
        beneficiaries = state[TransactionAgentStateFields.PROCESSED_TRANSACTIONS]
        selected_transaction = beneficiaries.get(choice_id)
        assert selected_transaction, f"Beneficiary with id {choice_id} not found"
        return {
            TransactionAgentStateFields.MESSAGES: [
                HumanMessage(
                    content=f"My selected beneficiary is: {selected_transaction[0].counterparty_name}"
                )
            ],
            TransactionAgentStateFields.CONFIRMED_TRANSACTIONS: selected_transaction,
            TransactionAgentStateFields.PROCESSED_TRANSACTIONS: [],
            TransferAgentStateFields.RESUME_NODE: None,
        }
    except Exception as e:
        logger.error(f"Failed to select beneficiary: {e}")
        raise
