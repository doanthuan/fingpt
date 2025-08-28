from langchain.tools import StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnableConfig

from app.assistant_v2.common.base_agent_config import BaseAgentConfig
from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, CONTEXT_KEY
from app.core.context import RequestContext
from app.utils.modified_langfuse_decorator import observe  # type: ignore


class ReportGeneratorInput(BaseModel):
    ticker_symbol: str = Field(
        description="The ticker symbol of the public company for which to generate the report",
    )


@observe()
async def report_generator(
    ticker_symbol: str,
    config: RunnableConfig,
) -> str:
    config_data: BaseAgentConfig = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()
    logger.debug("Returning dummy report...")
    return f"The full report has been generated for {ticker_symbol}."


REPORT_GENERATOR_NAME = "ReportGenerator"

report_generator_tool: StructuredTool = StructuredTool.from_function(  # type: ignore
    coroutine=report_generator,
    name=REPORT_GENERATOR_NAME,
    description="Generates a full report for a public company based on its ticker symbol.",
    args_schema=ReportGeneratorInput,
    error_on_invalid_docstring=True,
)
