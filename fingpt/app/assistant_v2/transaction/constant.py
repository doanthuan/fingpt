from typing import Any

from app.assistant_v2.util.complete_or_escalate import CompleteOrEscalateTool

from .tool.to_report_generator import ToReportGenerator

TRANSACTION_AGENT_TOOLS: list[Any] = [
    ToReportGenerator,
    CompleteOrEscalateTool,
]


TRANSACTION_REVIEW_DESCRIPTION = (
    "This graph depicts the transactions activity over the past {num_month} months"
    ". The green line represents the number of transactions with positive values indicating incoming "
    "transfer and negative values indicating outgoing transfer."
)

TRANSACTION_REVIEW_NO_DATA_CONTENT = "No transaction data found. Please try again!"

FILTER_TRANSACTION_TOOL_NAME = "FilterTransactionTool"
