from enum import Enum
from typing import Optional

from pydantic.v1 import BaseModel


class TermUnit(str, Enum):
    Y = "Y"
    M = "M"
    W = "W"
    D = "D"


class TermDepositProduct(BaseModel):
    id: str
    name: str
    interest_rate: float
    term_number: int
    term_unit: TermUnit
    minimum_required_balance: float = 0
    is_available: bool = False
    maturity_earn: float = 0


class AccountIdentification(BaseModel):
    bban: Optional[str] = ""
    bic: Optional[str] = ""


class ActiveAccount(BaseModel):
    id: str
    name: Optional[str]
    product_type: str
    product_kind_name: str = ""
    available_balance: float = ""
    currency: str
    identifications: Optional[AccountIdentification] = AccountIdentification()
    booked_balance: float = 0
    is_usable: bool = True


class TermDepositAccount(BaseModel):
    id: str
    name: str
    interest_rate: float
    term_number: int
    term_unit: TermUnit
    maturity_date: str
    start_date: str
    bban: str
    deposit_amount: float
    maturity_earn: float = 0.0
    is_renewable: bool = False
    is_mature: bool = False
