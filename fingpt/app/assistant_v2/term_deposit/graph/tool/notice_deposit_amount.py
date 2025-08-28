from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools.structured import StructuredTool

from app.assistant_v2.term_deposit.constant import NOTICE_DEPOSIT_AMOUNT_TOOL_NAME
from app.utils.modified_langfuse_decorator import observe


class NoticeDepositAmountInput(BaseModel):
    deposit_amount: float = Field(
        description="The deposit amount for creating (opening) new term deposit or renewing term deposit.",
    )


@observe()
async def _notice_deposit_amount(
    deposit_amount: float,
) -> str:
    if deposit_amount < 0:
        raise ValueError("Amount cannot be negative")
    return str(deposit_amount)


notice_desposit_amount_tool: StructuredTool = StructuredTool.from_function(
    coroutine=_notice_deposit_amount,
    name=NOTICE_DEPOSIT_AMOUNT_TOOL_NAME,
    description=(
        "Call this function to get the deposit amount for creating (opening) new term deposit or renewing term deposit."
    ),
    args_schema=NoticeDepositAmountInput,
    error_on_invalid_docstring=True,
)
