from typing import Any, Dict

from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig

from app.assistant_v2.card.state import CardAgentState, CardAgentStateFields
from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    PENDING_RESPONSE_KEY,
    THREAD_ID_KEY,
)
from app.core import RequestContext
from app.entity import Card, ChatRespAction, ChatRespDto
from app.entity.chat_response import ChatRespMetadataForRenewCard
from app.utils.modified_langfuse_decorator import observe

review_card_node = NodeName("review_card")


@observe()
async def review_card_func(
    state: CardAgentState,
    config: RunnableConfig,
) -> Dict[str, Any]:
    config_data = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()
    logger.info("Reviewing card...")
    renewable_card: Card = list(state[CardAgentStateFields.RENEWABLE_CARDS].values())[0]
    last_message = state[CardAgentStateFields.MESSAGES][-1]

    output = {}
    response = ChatRespDto(
        action=ChatRespAction.RENEW_CARD,
        thread_id=config_data[THREAD_ID_KEY],
        response=last_message.content,
        metadata=ChatRespMetadataForRenewCard(
            card=renewable_card.dict(),
        ),
    )
    output[CardAgentStateFields.MESSAGES] = [HumanMessage(content="It's okay.")]

    config_data[PENDING_RESPONSE_KEY].append(response)
    # reset state
    output[CardAgentStateFields.RESUME_NODE] = None
    output[CardAgentStateFields.RENEWABLE_CARDS] = {}
    output[CardAgentStateFields.HUMAN_APPROVAL_RENEWABLE_CARD] = False
    return output
