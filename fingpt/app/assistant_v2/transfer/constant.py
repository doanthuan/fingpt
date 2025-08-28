from typing import Any

from app.assistant_v2.transfer.tool.to_transfer_money_flow import ToMoneyTransferFlow
from app.assistant_v2.util.complete_or_escalate import CompleteOrEscalateTool

MESSAGE_CONTENT = "content"

TRANSFER_AGENT_TOOLS: list[Any] = [
    ToMoneyTransferFlow,
    CompleteOrEscalateTool,
]

NOTICE_TRANSFER_AMOUNT_TOOL_NAME = "NoticeTransferAmountTool"
GET_CONTACT_TOOL_NAME = "GetContactTool"
GET_ACCOUNT_TOOL_NAME = "GetAccountTool"
