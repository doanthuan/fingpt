from typing import Any, Optional

from attr import dataclass

from app.assistant_v2.common.base_agent_config import BaseAgentConfig
from app.assistant_v2.common.base_agent_state import (
    BaseAgentState,
    BaseAgentStateFields,
)
from app.entity.api import SupportedTicker
from app.finance.fin_service import FinService
from app.finance.sec_service import SecService


class TickerAgentState(BaseAgentState):
    symbol: Optional[SupportedTicker]

    company_info: Optional[dict[str, Any]]
    income_stmt: Optional[str]
    balance_sheet: Optional[str]
    cash_flow: Optional[str]
    section_7: Optional[str]

    income_stmt_report: Optional[str]
    balance_sheet_report: Optional[str]
    cash_flow_report: Optional[str]
    summary_report: Optional[str]


@dataclass
class TickerAgentStateFields(BaseAgentStateFields):
    SYMBOL = "symbol"

    COMPANY_INFO = "company_info"
    INCOME_STMT = "income_stmt"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    SECTION_7 = "section_7"

    INCOME_STMT_REPORT = "income_stmt_report"
    BALANCE_SHEET_REPORT = "balance_sheet_report"
    CASH_FLOW_REPORT = "cash_flow_report"
    SUMMARY_REPORT = "summary_report"


TickerAgentStateFields.validate_agent_fields(TickerAgentState)


class TickerAgentConfig(BaseAgentConfig):
    fs: FinService
    ss: SecService
    sec_api_key: str
