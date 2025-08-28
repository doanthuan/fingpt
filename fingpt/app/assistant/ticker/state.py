import operator
from typing import Annotated, Any, Optional, Sequence

from langchain_core.messages import AnyMessage
from langchain_openai import AzureChatOpenAI
from typing_extensions import TypedDict

from app.core.context import RequestContext
from app.finance.fin_service import FinService
from app.finance.sec_service import SecService
from app.prompt.prompt_service import PromptService


class TickerAgentState(TypedDict):
    messages: Annotated[
        Sequence[AnyMessage],
        operator.add,
    ]

    responses: Annotated[
        Sequence[str],
        operator.add,
    ]

    user_query: Optional[str]
    symbol: Optional[str]

    company_info: Optional[dict[str, Any]]
    income_stmt: Optional[str]
    balance_sheet: Optional[str]
    cash_flow: Optional[str]
    section_7: Optional[str]

    income_stmt_report: Optional[str]
    balance_sheet_report: Optional[str]
    cash_flow_report: Optional[str]
    summary_report: Optional[str]


class TickerAgentConfig(TypedDict):
    _fs: FinService
    _ss: SecService
    _ps: PromptService
    _llm_model: AzureChatOpenAI

    _ctx: Optional[RequestContext]
    _sec_api_key: Optional[str]
