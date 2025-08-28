from typing import Any, Dict

from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.card.state import CardAgentState, CardAgentStateFields
from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    USER_CHOICE_ID_KEY,
)
from app.core import RequestContext
from app.utils.modified_langfuse_decorator import observe

select_renewable_card_node = NodeName("select_renewable_card")


@observe()
async def select_renewable_card_func(
    state: CardAgentState,
    config: RunnableConfig,
) -> Dict[str, Any]:
    config_data = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()
    logger.info(
        f"Selecting renewable card... User choice: {config_data[USER_CHOICE_ID_KEY]}"
    )
    try:
        choice_id: str = config_data[USER_CHOICE_ID_KEY] or ""
        assert choice_id != "", "User choice is empty"
        renewable_cards = state[CardAgentStateFields.RENEWABLE_CARDS]
        renewable_card = renewable_cards[choice_id]
        message = HumanMessage(f"Selected renewable card id: {renewable_card.id}")
        return {
            CardAgentStateFields.MESSAGES: [message],
            CardAgentStateFields.RENEWABLE_CARDS: {choice_id: renewable_card},
            CardAgentStateFields.HUMAN_APPROVAL_RENEWABLE_CARD: True,
            CardAgentStateFields.RESUME_NODE: None,
        }

    except Exception as e:
        logger.error(f"Failed to select term deposit product: {e}")
        raise
