from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools.structured import StructuredTool

from app.assistant_v2.transfer.constant import NOTICE_TRANSFER_AMOUNT_TOOL_NAME
from app.utils.modified_langfuse_decorator import observe


class NoticeTransferAmountInput(BaseModel):
    amount: float = Field(
        description="The amount to be transferred, this value must not be null",
    )


@observe()
async def _notice_transfer_amount(
    amount: float,
) -> str:
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    return str(amount)


notice_transfer_amount_tool: StructuredTool = StructuredTool.from_function(
    coroutine=_notice_transfer_amount,
    name=NOTICE_TRANSFER_AMOUNT_TOOL_NAME,
    description="Call this function to get the amount of money to be transferred",
    args_schema=NoticeTransferAmountInput,
    error_on_invalid_docstring=True,
)
