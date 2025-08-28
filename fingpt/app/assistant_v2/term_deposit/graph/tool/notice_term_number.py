from typing import Optional

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools.structured import StructuredTool

from app.assistant_v2.term_deposit.constant import NOTICE_TERM_NUMBER_TOOL_NAME
from app.utils.modified_langfuse_decorator import observe


class NoticeTermNumberInput(BaseModel):
    term_number: Optional[int] = Field(
        description="The term number for creating (opening) new term deposit or renewing term deposit."
        "This is a optional field, if user does not provide the term number at the beginning, "
        "just ignore and leave it as None.",
    )


@observe()
async def _notice_term_number(
    term_number: float,
) -> str:
    return str(term_number)


notice_term_number_tool: StructuredTool = StructuredTool.from_function(
    coroutine=_notice_term_number,
    name=NOTICE_TERM_NUMBER_TOOL_NAME,
    description=(
        "Call this function to get the term number for creating (opening) new term deposit or renewing term deposit."
    ),
    args_schema=NoticeTermNumberInput,
    error_on_invalid_docstring=True,
)
