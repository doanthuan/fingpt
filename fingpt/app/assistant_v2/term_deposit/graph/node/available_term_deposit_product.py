from typing import Any, Dict

from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import PENDING_RESPONSE_KEY, THREAD_ID_KEY
from app.assistant_v2.term_deposit.graph.node.select_term_deposit_product import (
    select_term_deposit_product_node,
)
from app.assistant_v2.term_deposit.graph.utils import (
    _build_choices_from_term_deposit_products,
)
from app.assistant_v2.term_deposit.state import (
    TermDepositAgentState,
    TermDepositAgentStateFields,
)
from app.assistant_v2.util.misc import extract_config
from app.entity import ChatRespAction, ChatRespDto
from app.utils.modified_langfuse_decorator import observe

available_term_deposit_product_node = NodeName("available_term_deposit_product")


@observe()
async def available_term_deposit_product_func(
    state: TermDepositAgentState,
    config: RunnableConfig,
) -> Dict[str, Any]:
    config_data, _, logger = extract_config(config)
    logger.info("Available term deposit products...")
    last_message = state[TermDepositAgentStateFields.MESSAGES][-1]
    response = ChatRespDto(
        action=ChatRespAction.SHOW_CHOICES,
        thread_id=config_data[THREAD_ID_KEY],
        response=last_message.content,
        metadata=_build_choices_from_term_deposit_products(
            state[TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS],
        ),
    )
    config_data[PENDING_RESPONSE_KEY].append(response)
    if any([c.is_enabled for c in response.metadata.choices]):
        return {
            TermDepositAgentStateFields.RESUME_NODE: select_term_deposit_product_node,
        }
    return {
        TermDepositAgentStateFields.MESSAGES: [],
    }
