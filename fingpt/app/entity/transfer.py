from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.entity.term_deposit import ActiveAccount


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class Contact(BaseModel):
    id: str
    name: str
    account_number: Optional[str] = None
    phone_number: Optional[str] = None
    email_address: Optional[str] = None
    iban: Optional[str] = None


class ContactRespDto(BaseModel):
    account: list[ActiveAccount]
    recipient: list[Contact]
    amount: float
