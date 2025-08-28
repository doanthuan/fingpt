from enum import Enum
from typing import Any, Generic, Optional, TypeVar, Union

from pydantic import BaseModel

from app.entity.transfer import Currency

T = TypeVar("T")


class Intent(str, Enum):
    ABORT = "ABORT"
    UNKNOWN = "UNKNOWN"
    MONEY_TRANSFER = "MONEY_TRANSFER"


class FieldStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    NOT_FOUND = "NOT_FOUND"
    INVALID = "INVALID"


class FieldData(BaseModel, Generic[T]):
    status: FieldStatus
    value: Optional[T] = None


class IntentMetadataType(str, Enum):
    MONEY_TRANSFER_DATA = "MONEY_TRANSFER_DATA"
    ABORT_DATA = "ABORT_DATA"
    UNKNOWN_DATA = "UNKNOWN_DATA"


class IntentRespMetadataBaseType(BaseModel):
    type: IntentMetadataType


class IntentMetadataForMoneyTransfer(IntentRespMetadataBaseType):
    type: IntentMetadataType = IntentMetadataType.MONEY_TRANSFER_DATA
    amount: FieldData[float]
    currency: FieldData[Currency]
    recipient: FieldData[dict[str, Any]]
    account: FieldData[dict[str, Any]]


class IntentMetadataForAbort(IntentRespMetadataBaseType):
    type: IntentMetadataType = IntentMetadataType.ABORT_DATA
    reason: FieldData[str]


class IntentMetadataForUnknown(IntentRespMetadataBaseType):
    type: IntentMetadataType = IntentMetadataType.UNKNOWN_DATA


# Response


class IntentRespDto(BaseModel):
    intent: Intent
    metadata: Union[
        IntentMetadataForMoneyTransfer,
        IntentMetadataForAbort,
        IntentMetadataForUnknown,
    ]


# Request


class IntentReqDto(BaseModel):
    messages: list[str]
    metadata: Optional[IntentRespDto] = None
