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

select_term_deposit_product_node = NodeName("select_term_deposit_product")


@observe()
async def select_term_deposit_product_func(
    state: TermDepositAgentState, config: RunnableConfig
) -> Dict[str, Any]:
    config_data, _, logger = extract_config(config)
    logger.info(
        f"Selecting term deposit product... User choice: {config_data[USER_CHOICE_ID_KEY]}"
    )
    try:
        choice_id: str = config_data[USER_CHOICE_ID_KEY] or ""
        assert choice_id != "", "User choice is empty"
        term_deposit_products = state[TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS]
        term_deposit_product = term_deposit_products[choice_id]
        action = state.get(TermDepositAgentStateFields.ACTION, None)
        logger.info(f"Action: {action}")
        if action == "get_offer":
            message = HumanMessage(
                f"Selected term deposit product: {term_deposit_product.name}. "
                "You MUST NOT call any tools. Just return 'Let's review your renewal information'."
            )
            return {
                TermDepositAgentStateFields.MESSAGES: [message],
                TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS: {
                    choice_id: term_deposit_product
                },
                TermDepositAgentStateFields.HUMAN_APPROVAL_PRESENT_OFFER: True,
                TermDepositAgentStateFields.RESUME_NODE: None,
            }
        else:
            message = HumanMessage(
                f"Selected term deposit product: {term_deposit_product.name}"
            )
            return {
                TermDepositAgentStateFields.MESSAGES: [message],
                TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS: {
                    choice_id: term_deposit_product
                },
                TermDepositAgentStateFields.HUMAN_APPROVAL_TERM_DEPOSIT_PRODUCT: True,
                TermDepositAgentStateFields.RESUME_NODE: None,
            }
    except Exception as e:
        logger.error(f"Failed to select term deposit product: {e}")
        raise
