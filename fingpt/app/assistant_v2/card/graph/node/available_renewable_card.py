from typing import Any, Dict

from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.card.graph.node.select_renewable_card import (
    select_renewable_card_node,
)
from app.assistant_v2.card.graph.utils import _build_choices_from_card_list
from app.assistant_v2.card.state import CardAgentState, CardAgentStateFields
from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    PENDING_RESPONSE_KEY,
    THREAD_ID_KEY,
)
from app.core import RequestContext
from app.entity import ChatRespAction, ChatRespDto
from app.utils.modified_langfuse_decorator import observe

available_renewable_card_node = NodeName("available_renewable_card")


@observe()
async def available_renewable_card_func(
    state: CardAgentState,
    config: RunnableConfig,
) -> Dict[str, Any]:
    config_data = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()
    logger.info("Available renewable cards...")
    last_message = state[CardAgentStateFields.MESSAGES][-1]
    response = ChatRespDto(
        action=ChatRespAction.SHOW_CHOICES,
        thread_id=config_data[THREAD_ID_KEY],
        response=last_message.content,
        metadata=_build_choices_from_card_list(
            state[CardAgentStateFields.RENEWABLE_CARDS],
        ),
    )
    config_data[PENDING_RESPONSE_KEY].append(response)
    return {
        CardAgentStateFields.RESUME_NODE: select_renewable_card_node,
    }
