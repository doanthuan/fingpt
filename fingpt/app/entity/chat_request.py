from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel

from app.entity.offer import OfferReq


class ChatReqAction(str, Enum):
    QUERY = "QUERY"
    MAKE_CHOICE = "MAKE_CHOICE"  # only 1 choice
    MAKE_SELECTION = "MAKE_SELECTION"  # multiple selects
    GET_OFFER = "GET_OFFER"


class ChatReqMetadataType(str, Enum):
    QUERY_DATA = "QUERY_DATA"
    CHOICE_DATA = "CHOICE_DATA"
    SELECTION_DATA = "SELECTION_DATA"
    OFFER_DATA = "OFFER_DATA"


class ChatReqMetadataBaseType(BaseModel):
    type: ChatReqMetadataType


class ChatReqMetadataForQuery(ChatReqMetadataBaseType):
    type: ChatReqMetadataType = ChatReqMetadataType.QUERY_DATA
    thread_id: Optional[str] = None
    user_query: str


class ChatReqMetadataForChoice(ChatReqMetadataBaseType):
    type: ChatReqMetadataType = ChatReqMetadataType.CHOICE_DATA
    thread_id: str
    choice_id: str


class ChatReqMetadataForSelect(ChatReqMetadataBaseType):
    type: ChatReqMetadataType = ChatReqMetadataType.SELECTION_DATA
    thread_id: str
    selection_ids: list[str]


class ChatReqMetadataForOffer(ChatReqMetadataBaseType):
    type: ChatReqMetadataType = ChatReqMetadataType.OFFER_DATA
    thread_id: Optional[str] = None
    offer: OfferReq


class ChatReqDto(BaseModel):
    action: ChatReqAction
    metadata: Union[
        ChatReqMetadataForQuery,
        ChatReqMetadataForChoice,
        ChatReqMetadataForSelect,
        ChatReqMetadataForOffer,
    ]
