from typing import Any

from attr import dataclass

from app.assistant_v2.common.base_agent_config import BbRetailAgentConfig
from app.assistant_v2.common.base_agent_state import (
    BaseAgentState,
    BaseAgentStateFields,
)
from app.entity.api import SupportedTicker
from app.entity.assistant import AssistantStatus

from .constant import DialogController


class AssistantState(BaseAgentState):
    controller_stack: list[DialogController]
    status: AssistantStatus

    symbol: SupportedTicker

    term_deposit_agent_state: dict[str, Any]
    card_agent_state: dict[str, Any]
    transaction_report_agent_state: dict[str, Any]
    transfer_agent_state: dict[str, Any]
    last_summary_message_id: str


@dataclass
class AssistantStateFields(BaseAgentStateFields):
    CONTROLLER_STACK = "controller_stack"
    STATUS = "status"

    SYMBOL = "symbol"

    TERM_DEPOSIT_AGENT_STATE = "term_deposit_agent_state"
    CARD_AGENT_STATE = "card_agent_state"
    TRANSACTION_REPORT_AGENT_STATE = "transaction_report_agent_state"
    TRANSFER_AGENT_STATE = "transfer_agent_state"
    LAST_SUMMARY_MESSAGE_ID = "last_summary_message_id"


AssistantStateFields.validate_agent_fields(AssistantState)


class AssistantConfig(BbRetailAgentConfig):
    pass


agent_state_key_map: dict[DialogController, str] = {
    "TRANSACTION_AGENT": AssistantStateFields.TRANSACTION_REPORT_AGENT_STATE,
    "TERM_DEPOSIT_CONTROLLER": AssistantStateFields.TERM_DEPOSIT_AGENT_STATE,
    "CARD_CONTROLLER": AssistantStateFields.CARD_AGENT_STATE,
    "TRANSFER_AGENT": AssistantStateFields.TRANSFER_AGENT_STATE,
}
