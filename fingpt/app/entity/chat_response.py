from enum import Enum
from typing import Any, Dict, Optional, Sequence, Union

from pydantic import BaseModel

from app.entity import SupportedTicker
from app.entity.offer import OfferResp


class ChatRespAction(str, Enum):
    SHOW_REPLY = "SHOW_REPLY"
    SHOW_CHOICES = "SHOW_CHOICES"  # use for only 1 choice
    SHOW_SELECTION = "SHOW_SELECTION"  # use for multiple selects
    SHOW_OFFER = "SHOW_OFFER"
    MAKE_TRANSFER = "MAKE_TRANSFER"
    MAKE_TERM_DEPOSIT = "MAKE_TERM_DEPOSIT"
    RENEW_CARD = "RENEW_CARD"
    SHOW_TICKER_REPORT = "SHOW_TICKER_REPORT"
    RENEW_TERM_DEPOSIT = "RENEW_TERM_DEPOSIT"


class ChatRespMetadataType(str, Enum):
    IMAGE_DATA = "IMAGE_DATA"
    CHOICE_DATA = "CHOICE_DATA"
    CHOICES_DATA = "CHOICES_DATA"
    SELECT_DATA = "SELECT_DATA"
    SELECTION_DATA = "SELECTION_DATA"
    OFFER_DATA = "OFFER_DATA"
    TRANSFER_DATA = "TRANSFER_DATA"
    TERM_DEPOSIT_DATA = "TERM_DEPOSIT_DATA"
    RENEW_CARD_DATA = "RENEW_CARD_DATA"
    SHOW_TICKER_REPORT_DATA = "SHOW_TICKER_REPORT_DATA"
    TRANSACTION_DATA = "TRANSACTION_DATA"


class ChatRespChoiceMetadataType(str, Enum):
    BENEFICIARY_CHOICE = "BENEFICIARY_CHOICE"
    BENIFICIARY_TYPO_CHOICE = "BENIFICIARY_CHOICE"
    CONTACT_CHOICE = "CONTACT_CHOICE"
    ACCOUNT_CHOICE = "ACCOUNT_CHOICE"
    TERM_DEPOSIT_REVIEW_CHOICE = "TERM_DEPOSIT_CHOICE"
    CARD_CHOICE = "CARD_CHOICE"
    TERM_DEPOSIT_PRODUCT_CHOICE = "TERM_DEPOSIT_PRODUCT_CHOICE"


class ChatRespTermDepositLabel(str, Enum):
    DEFAULT = ""
    BEST_CHOICE = "Best choice"
    NEW = "New"


class TransactionChartData(BaseModel):
    month: str
    transaction_count: int
    income: float
    outcome: float


class ChatRespMetadataBaseType(BaseModel):
    type: ChatRespMetadataType


# TODO Clean this up
class ChatRespMetadataForImage(ChatRespMetadataBaseType):
    type: ChatRespMetadataType = ChatRespMetadataType.IMAGE_DATA
    image_url: str
    description: str


class ChatRespMetadataForTransaction(ChatRespMetadataBaseType):
    type: ChatRespMetadataType = ChatRespMetadataType.TRANSACTION_DATA
    chart_data: Sequence[TransactionChartData]
    description: str


class ChatRespMetadataForChoiceBaseType(BaseModel):
    type: ChatRespChoiceMetadataType
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: bool = True
    label: ChatRespTermDepositLabel = ChatRespTermDepositLabel.DEFAULT


class ChatRespMetadataForContactChoice(ChatRespMetadataForChoiceBaseType):
    type: ChatRespChoiceMetadataType = ChatRespChoiceMetadataType.CONTACT_CHOICE
    account_number: str


class ChatRespMetadataForBeneficiaryChoice(ChatRespMetadataForChoiceBaseType):
    type: ChatRespChoiceMetadataType = ChatRespChoiceMetadataType.BENEFICIARY_CHOICE
    account_number: str


class ChatRespMetadataForAccountChoice(ChatRespMetadataForChoiceBaseType):
    type: ChatRespChoiceMetadataType = ChatRespChoiceMetadataType.ACCOUNT_CHOICE
    product_type: str
    available_balance: float
    currency: str
    bban: Optional[str] = None
    booked_balance: Optional[float] = None


class ChatRespMetadataForTermDepositProductChoice(ChatRespMetadataForChoiceBaseType):
    type: ChatRespChoiceMetadataType = (
        ChatRespChoiceMetadataType.TERM_DEPOSIT_PRODUCT_CHOICE
    )
    interest_rate: float
    term_number: int
    term_unit: str
    minimum_required_balance: float
    maturity_earn: float


class ChatRespMetadataForTermDepositReviewChoice(ChatRespMetadataForChoiceBaseType):
    type: ChatRespChoiceMetadataType = (
        ChatRespChoiceMetadataType.TERM_DEPOSIT_REVIEW_CHOICE
    )
    interest_rate: float
    term_number: int
    term_unit: str
    maturity_date: str
    deposit_amount: float


class ChatRespMetadataForCardChoice(ChatRespMetadataForChoiceBaseType):
    type: ChatRespChoiceMetadataType = ChatRespChoiceMetadataType.CARD_CHOICE
    brand: str
    card_type: str
    status: str
    lock_status: str | None
    replacement_status: str | None
    holder_name: str | None
    currency: str
    expiry_date: str


class ChatRespMetadataForChoices(ChatRespMetadataBaseType):
    type: ChatRespMetadataType = ChatRespMetadataType.CHOICES_DATA
    choices: Sequence[
        Union[
            ChatRespMetadataForChoiceBaseType,
            ChatRespMetadataForContactChoice,
            ChatRespMetadataForAccountChoice,
            ChatRespMetadataForTermDepositProductChoice,
            ChatRespMetadataForCardChoice,
            ChatRespMetadataForTermDepositReviewChoice,
        ]
    ]


class ChatRespMetadataForSelect(ChatRespMetadataBaseType):
    type: ChatRespMetadataType = ChatRespMetadataType.SELECT_DATA
    id: str
    name: str


class ChatRespMetadataForSelection(ChatRespMetadataBaseType):
    type: ChatRespMetadataType = ChatRespMetadataType.SELECTION_DATA
    selection: Sequence[ChatRespMetadataForSelect]


class ChatRespMetadataForTransfer(ChatRespMetadataBaseType):
    type: ChatRespMetadataType = ChatRespMetadataType.TRANSFER_DATA
    account: Dict[str, Any]
    recipient: Dict[str, Any]
    transfer_amount: float


class ChatRespMetadataForTermDeposit(ChatRespMetadataBaseType):
    type: ChatRespMetadataType = ChatRespMetadataType.TERM_DEPOSIT_DATA
    id: str
    deposit_amount: float
    interest_rate: float
    term_number: int
    term_unit: str
    maturity_earn: float
    active_account: Dict[str, Any] | None
    renewal_account: Dict[str, Any] | None
    maturity_date: str | None
    date_of_renewal: str | None
    start_date: str | None


class ChatRespMetadataForRenewCard(ChatRespMetadataBaseType):
    type: ChatRespMetadataType = ChatRespMetadataType.RENEW_CARD_DATA
    card: Dict[str, Any]


class ChatRespMetadataForShowTickerReport(ChatRespMetadataBaseType):
    type: ChatRespMetadataType = ChatRespMetadataType.SHOW_TICKER_REPORT_DATA
    ticker: SupportedTicker


class ChatRespMetadataForOffer(ChatRespMetadataBaseType):
    type: ChatRespMetadataType = ChatRespMetadataType.OFFER_DATA
    offer: OfferResp


class ChatRespDto(BaseModel):
    thread_id: Optional[str] = None
    response: str
    action: ChatRespAction
    metadata: Union[
        ChatRespMetadataForImage,
        ChatRespMetadataForChoices,
        ChatRespMetadataForTransfer,
        ChatRespMetadataForShowTickerReport,
        ChatRespMetadataForTermDeposit,
        ChatRespMetadataForTransaction,
        ChatRespMetadataForRenewCard,
        ChatRespMetadataForOffer,
        None,
    ]
