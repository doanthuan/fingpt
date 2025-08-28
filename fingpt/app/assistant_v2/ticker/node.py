from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig

from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    PROMPT_SERVICE_KEY,
)
from app.assistant_v2.ticker.state import TickerAgentStateFields
from app.core.config import settings
from app.core.context import RequestContext
from app.prompt.prompt_service import PromptService
from app.utils.modified_langfuse_decorator import observe  # type: ignore

from .state import TickerAgentConfig, TickerAgentState


@observe()
async def income_stmt_analyst(
    state: TickerAgentState,
    config: RunnableConfig,
) -> dict[str, Any]:
    config_data: TickerAgentConfig = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    ps: PromptService = config_data[PROMPT_SERVICE_KEY]
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()
    logger.debug("Starting income analyst agent...")

    try:
        prompt = await ps.get_prompt(
            ctx,
            name=settings.ticker_report_analyze_income_stmt_prompt,
            type="chat",
            label=settings.ticker_report_analyze_income_stmt_label,
        )

        chain = prompt.tmpl | prompt.llm_model | StrOutputParser()  # type: ignore

        logger.debug("Calling chain...")
        response = await chain.ainvoke(  # type: ignore
            input={
                "income_stmt": state[TickerAgentStateFields.INCOME_STMT],
                "industry": state[TickerAgentStateFields.COMPANY_INFO]["industry"],  # type: ignore
                "section_text": state[TickerAgentStateFields.SECTION_7],
            },
        )

        logger.info("Returning income statement report...")
        return {
            TickerAgentStateFields.MESSAGES: [response],
            TickerAgentStateFields.INCOME_STMT_REPORT: response,
        }

    except Exception as e:
        logger.error(f"Error in income statement analyst: {e}")
        raise
