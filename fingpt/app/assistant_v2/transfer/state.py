from typing import Optional

from attr import dataclass

from app.assistant_v2.common.base_agent_config import BbRetailAgentConfig
from app.assistant_v2.common.base_agent_state import (
    BaseAgentState,
    BaseAgentStateFields,
)
from app.entity import ActiveAccount, Contact


class TransferAgentState(BaseAgentState):
    recipient_name: str
    transfer_amount: float
    contact_list: list[Contact]
    active_accounts: list[ActiveAccount]
    selected_contact: Optional[Contact]
    selected_account: Optional[ActiveAccount]


@dataclass
class TransferAgentStateFields(BaseAgentStateFields):
    RECIPIENT_NAME = "recipient_name"
    TRANSFER_AMOUNT = "transfer_amount"
    CONTACT_LIST = "contact_list"
    ACTIVE_ACCOUNTS = "active_accounts"
    SELECTED_CONTACT = "selected_contact"
    SELECTED_ACCOUNT = "selected_account"


class TransferAgentConfig(BbRetailAgentConfig):
    pass


TransferAgentStateFields.validate_agent_fields(TransferAgentState)
