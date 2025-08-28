from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel

from app.entity.card import Card


class OfferProduct(str, Enum):
    TERM_DEPOSIT = "TERM_DEPOSIT"
    CARD = "CARD"


class OfferType(str, Enum):
    RENEWAL = "RENEWAL"


class OfferReqDataForTermDeposit(BaseModel):
    type: OfferType
    deposit_id: str


class OfferReqDataForCard(BaseModel):
    type: OfferType
    card_id: str


class OfferRespDataForCard(BaseModel):
    type: OfferType
    card: Optional[Card]


class OfferRespDataForTermDeposit(BaseModel):
    type: OfferType
    deposit_id: str


class OfferReq(BaseModel):
    product: OfferProduct
    message: str
    data: Union[
        OfferReqDataForTermDeposit,
        OfferReqDataForCard,
    ]


class OfferResp(BaseModel):
    product: OfferProduct
    message: Optional[str]
    data: Union[
        OfferRespDataForTermDeposit,
        OfferRespDataForCard,
    ]
