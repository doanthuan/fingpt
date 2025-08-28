from typing import Optional

from attr import dataclass

from app.assistant_v2.common.base_agent_state import (
    BaseAgentState,
    BaseAgentStateFields,
)
from app.entity import Card


class CardAgentState(BaseAgentState):
    renewable_cards: dict[str, Card]
    human_approval_renewable_card: Optional[bool]


@dataclass
class CardAgentStateFields(BaseAgentStateFields):
    RENEWABLE_CARDS = "renewable_cards"
    HUMAN_APPROVAL_RENEWABLE_CARD = "human_approval_renewable_card"


CardAgentStateFields.validate_agent_fields(CardAgentState)
