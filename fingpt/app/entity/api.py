import os
from enum import Enum
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class LlmName(str, Enum):
    GPT_4 = "gpt-4"


class AuthUserType(str, Enum):
    RETAIL = "retail"


class SupportedTicker(str, Enum):
    AAPL = "AAPL"
    ABBV = "ABBV"
    AMD = "AMD"
    AMZN = "AMZN"
    ASTS = "ASTS"
    AVGO = "AVGO"
    BFI = "BFI"
    CMAX = "CMAX"
    CMG = "CMG"
    BRK = "BRK-B"
    COUR = "COUR"
    DECK = "DECK"
    DOW = "DOW"
    DXCM = "DXCM"
    GOOG = "GOOG"
    GOOGL = "GOOGL"
    IBM = "IBM"
    HON = "HON"
    KLAC = "KLAC"
    LINE = "LINE"
    LLY = "LLY"
    LULU = "LULU"
    LW = "LW"
    MCD = "MCD"
    META = "META"
    MSFT = "MSFT"
    NOW = "NOW"
    NSC = "NSC"
    NVDA = "NVDA"
    OPTT = "OPTT"
    PLTR = "PLTR"
    POAI = "POAI"
    PYPL = "PYPL"
    RCL = "RCL"
    RTX = "RTX"
    SERV = "SERV"
    SGMO = "SGMO"
    SKX = "SKX"
    SMCI = "SMCI"
    TCS = "TCS"
    TSLA = "TSLA"
    TXRH = "TXRH"

    @classmethod
    def has_value(cls, value: str) -> bool:
        return value in cls._value2member_map_


class TickerReqDto(BaseModel):
    symbol: SupportedTicker = SupportedTicker.TSLA


class AuthReqDto(BaseModel):
    username: str = os.getenv("EBP_TEST_ACCOUNT_USERNAME") or ""
    password: str = "********"
    user_type: AuthUserType


class AuthRespDto(BaseModel):
    agreement_id: str
    edge_domain: str
    cookie: str
    access_token: str


class RawDataFormat(str, Enum):
    MARKDOWN = "MARKDOWN"
    CSV = "CSV"


class RawDataReqDto(BaseModel):
    symbol: SupportedTicker = SupportedTicker.TSLA
    raw_data_format: RawDataFormat = RawDataFormat.CSV


class TransactionReportReqDto(BaseModel):
    user_query: str = "Show me all the recent restaurant transactions?"
    thread_id: Optional[str]


class ApiHeader(BaseModel):
    cookie: str
    token: str
