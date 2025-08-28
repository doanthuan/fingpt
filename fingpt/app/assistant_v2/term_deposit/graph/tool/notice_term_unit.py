from typing import Optional

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools.structured import StructuredTool

from app.assistant_v2.term_deposit.constant import NOTICE_TERM_UNIT_TOOL_NAME
from app.utils.modified_langfuse_decorator import observe


class NoticeTermUnitInput(BaseModel):
    term_unit: Optional[str] = Field(
        description="The term unit for creating (opening) new term deposit or renewing term deposit."
        "The value MUST be one of the following: 'Y', 'M', 'W', 'D', with the following meanings: "
        "'Y' - year, 'M' - month, 'W' - week, 'D' - day. "
        "This is a optional field, if user does not provide the term unit at the beginning, "
        "just ignore and leave it as None.",
    )


@observe()
async def _notice_term_unit(
    term_unit: str,
) -> str:
    return str(term_unit)


notice_term_unit_tool: StructuredTool = StructuredTool.from_function(
    coroutine=_notice_term_unit,
    name=NOTICE_TERM_UNIT_TOOL_NAME,
    description=(
        "Call this function to get the term unit for creating (opening) new term deposit or renewing term deposit."
    ),
    args_schema=NoticeTermUnitInput,
    error_on_invalid_docstring=True,
)
