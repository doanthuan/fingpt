from langchain.tools import StructuredTool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnableConfig

from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    PROMPT_SERVICE_KEY,
)
from app.core.config import settings
from app.core.context import RequestContext
from app.prompt.prompt_service import PromptService
from app.utils.modified_langfuse_decorator import observe  # type: ignore

from ..state import TickerAgentConfig


class SymbolIdentifierInput(BaseModel):
    user_query: str = Field(
        description="The original user message from which to extra the ticker symbol",
    )


@observe()
async def symbol_identifier(
    user_query: str,
    config: RunnableConfig,
) -> str:
    config_data: TickerAgentConfig = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    ps: PromptService = config_data[PROMPT_SERVICE_KEY]
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()
    logger.debug("Extracting ticker symbol...")

    try:
        prompt = await ps.get_prompt(
            ctx,
            name=settings.ticker_report_symbol_detection_prompt,
            label=settings.ticker_report_symbol_detection_label,
            type="chat",
        )

        prompt_tmpl = prompt.tmpl
        chain = prompt_tmpl | prompt.llm_model | StrOutputParser()  # type: ignore

        response = await chain.ainvoke(  # type: ignore
            input={
                "user_query": [user_query],
            },
        )
        response = response.strip('"').strip("'").strip()

    except Exception as e:
        logger.error(f"Failed to get ticker symbol. Error: {e}")
        raise

    logger.info(f"Ticker symbol: {response}")
    return response


SYMBOL_IDENTIFIER_NAME = "TickerSymbolIdentifier"

symbol_identifier_tool: StructuredTool = StructuredTool.from_function(  # type: ignore
    coroutine=symbol_identifier,
    name=SYMBOL_IDENTIFIER_NAME,
    description="Useful to identify the exact ticker symbol from a message by the user",
    args_schema=SymbolIdentifierInput,
    error_on_invalid_docstring=True,
)
