import json
from typing import Any, Dict

from langchain_core.messages import ToolMessage

from app.assistant_v2.card.constant import GET_RENEWABLE_CARD_TOOL_NAME
from app.assistant_v2.card.state import CardAgentStateFields
from app.entity import Card, ChatRespMetadataForCardChoice, ChatRespMetadataForChoices


async def chain_ainvoke(chain, input_data: Dict[str, Any]):
    return await chain.ainvoke(input_data)


def extract_tool_messages(logger, messages) -> Dict[str, Any]:
    # get all recent tool messages
    logger.info("Card agent. Extracting data from tool message...")
    output = {}
    for message in messages[::-1]:
        if not isinstance(message, ToolMessage):
            break
        logger.debug(f"Card agent. Tool message: {message}")
        if message.name == GET_RENEWABLE_CARD_TOOL_NAME:
            output[CardAgentStateFields.RENEWABLE_CARDS] = {
                json.loads(account)["id"]: Card(**json.loads(account))
                for account in eval(message.content)
            }

    return output


def _build_choices_from_card_list(
    cards: dict[str, Card],
) -> ChatRespMetadataForChoices:
    return ChatRespMetadataForChoices(
        choices=[
            ChatRespMetadataForCardChoice(
                id=card.id,
                brand=card.brand,
                card_type=card.card_type,
                status=card.status,
                lock_status=card.lock_status,
                replacement_status=card.replacement_status,
                holder_name=card.holder_name,
                currency=card.currency,
                expiry_date=card.expiry_date,
            )
            for card in cards.values()
        ]
    )
