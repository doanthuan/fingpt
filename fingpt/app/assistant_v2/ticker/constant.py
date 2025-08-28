from typing import Any

from app.assistant_v2.util.complete_or_escalate import CompleteOrEscalateTool

from .tool.report_generator import report_generator_tool
from .tool.symbol_identifier import symbol_identifier_tool

TICKER_AGENT_TOOLS: list[Any] = [
    symbol_identifier_tool,
    report_generator_tool,
    CompleteOrEscalateTool,
]

UNRECOGNIZED_SYMBOL_MESSAGE = (
    "We are not able to recognize the symbol you mentioned. "
    "Please try again with a different symbol or company name."
)

UNSUPPORTED_SYMBOL_MESSAGE = (
    'We currently do not support the symbol "{symbol}". '
    "Please try again with a different symbol or company name."
)
