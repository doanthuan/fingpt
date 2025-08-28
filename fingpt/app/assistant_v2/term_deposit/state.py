from typing import Literal, Optional

from attr import dataclass

from app.assistant_v2.common.base_agent_state import (
    BaseAgentState,
    BaseAgentStateFields,
)
from app.entity import ActiveAccount, TermDepositAccount, TermDepositProduct, TermUnit


class TermDepositAgentState(BaseAgentState):
    deposit_amount: float
    term_number: int
    term_unit: TermUnit
    active_accounts: dict[str, ActiveAccount]
    term_deposit_products: dict[str, TermDepositProduct]
    term_deposit_accounts: dict[str, TermDepositAccount]
    action: Literal["new", "renew", "get_offer", "other"]
    human_approval_active_account: Optional[bool]
    human_approval_term_deposit_account: Optional[bool]
    human_approval_term_deposit_product: Optional[bool]
    human_approval_present_offer: Optional[bool]


@dataclass
class TermDepositAgentStateFields(BaseAgentStateFields):
    DEPOSIT_AMOUNT = "deposit_amount"
    TERM_NUMBER = "term_number"
    TERM_UNIT = "term_unit"
    ACTIVE_ACCOUNTS = "active_accounts"
    TERM_DEPOSIT_PRODUCTS = "term_deposit_products"
    TERM_DEPOSIT_ACCOUNTS = "term_deposit_accounts"
    ACTION = "action"
    HUMAN_APPROVAL_ACTIVE_ACCOUNT = "human_approval_active_account"
    HUMAN_APPROVAL_TERM_DEPOSIT_ACCOUNT = "human_approval_term_deposit_account"
    HUMAN_APPROVAL_TERM_DEPOSIT_PRODUCT = "human_approval_term_deposit_product"
    HUMAN_APPROVAL_PRESENT_OFFER = "human_approval_present_offer"


TermDepositAgentStateFields.validate_agent_fields(TermDepositAgentState)
