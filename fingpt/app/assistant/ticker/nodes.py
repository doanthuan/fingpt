import inspect
import json
from time import time
from typing import Any, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig

from app.assistant.ticker.state import TickerAgentState
from app.core.config import settings
from app.core.context import RequestContext
from app.entity import ChatRespAction, ChatRespDto, SupportedTicker
from app.entity.chat_response import ChatRespMetadataForShowTickerReport
from app.entity.finance_service import CachedReport
from app.finance.fin_service import FinService
from app.finance.sec_service import SecService
from app.prompt.prompt_service import PromptService
from app.utils.cache_manager import report_cache
from app.utils.modified_langfuse_decorator import observe  # type: ignore

CACHE_DIR = ".fin-gpt-cached"


def _invoke_chain(chain, input_data):
    return chain.ainvoke(input=input_data)  # type: ignore


@observe()
async def income_stmt_analyst(
    state: TickerAgentState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """
    This agent node is responsible for analyzing the income statement of a company.

    Args:
        state (AgentState): The state of the agent
        config (RunnableConfig): The configuration of the agent
    """
    ctx: RequestContext = config.get("configurable", {})["_ctx"]
    ps: PromptService = config.get("configurable", {})["_ps"]
    logger = ctx.logger()
    logger.debug("Starting income analyst agent...")
    try:
        logger.debug("Checking cache...")
        symbol = state["symbol"]
        assert symbol
        cache_file = report_cache.cache_file_path(symbol, inspect.stack()[0][3])
        report = await report_cache.load_cache(cache_file)
        if report:
            logger.info("Returning data from cache...")
            return {
                "messages": [report["data"]],
                "income_stmt_report": report["data"],
            }

    except Exception as e:
        logger.warn(f"Error loading cache: {e}. Continue...")

    prompt = await ps.get_prompt(
        ctx,
        name=settings.ticker_report_analyze_income_stmt_prompt,
        type="chat",
        label=settings.ticker_report_analyze_income_stmt_label,
    )

    assert "income_stmt" in state
    assert "company_info" in state
    assert "section_7" in state

    chain = prompt.tmpl | prompt.llm_model | StrOutputParser()  # type: ignore

    logger.debug("Calling chain...")
    response = await _invoke_chain(
        chain,
        input_data={
            "income_stmt": state["income_stmt"],
            "industry": state["company_info"]["industry"],
            "section_text": state["section_7"],
        },
    )
    try:
        logger.debug("Saving to cache...")
        report = CachedReport(ts=int(time()), data=response)
        symbol = state["symbol"]
        assert symbol
        cache_file = report_cache.cache_file_path(symbol, inspect.stack()[0][3])
        await report_cache.save_cache(report, cache_file)

    except Exception as e:
        logger.warn(f"Error saving cache: {e}. Continue...")

    logger.info("Returning income statement report...")
    return {
        "messages": [response],
        "income_stmt_report": response,
    }


@observe()
async def balance_sheet_analyst(
    state: TickerAgentState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """
    This agent node is responsible for analyzing the balance sheet of a company.

    Args:
        state (AgentState): The state of the agent
        config (RunnableConfig): The configuration of the agent
    """
    ctx: RequestContext = config.get("configurable", {})["_ctx"]
    ps: PromptService = config.get("configurable", {})["_ps"]
    logger = ctx.logger()
    logger.debug("Starting balance sheet analyst...")
    try:
        logger.debug("Checking cache...")
        symbol = state["symbol"]
        assert symbol
        cache_file = report_cache.cache_file_path(symbol, inspect.stack()[0][3])
        report = await report_cache.load_cache(cache_file)
        if report:
            logger.info("Returning data from cache...")
            return {
                "messages": [report["data"]],
                "balance_sheet_report": report["data"],
            }

    except Exception as e:
        logger.warn(f"Error loading cache: {e}. Continue...")

    prompt = await ps.get_prompt(
        ctx,
        name=settings.ticker_report_analyze_balance_sheet_prompt,
        type="chat",
        label=settings.ticker_report_analyze_balance_sheet_label,
    )

    assert "balance_sheet" in state
    assert "company_info" in state
    assert "section_7" in state

    chain = prompt.tmpl | prompt.llm_model | StrOutputParser()  # type: ignore

    logger.debug("Calling chain...")
    response = await _invoke_chain(
        chain,  # type: ignore
        input_data={
            "balance_sheet": state["balance_sheet"],
            "industry": state["company_info"]["industry"],
            "section_text": state["section_7"],
        },
    )
    try:
        logger.debug("Saving to cache...")
        report = CachedReport(ts=int(time()), data=response)
        symbol = state["symbol"]
        assert symbol
        cache_file = report_cache.cache_file_path(symbol, inspect.stack()[0][3])
        await report_cache.save_cache(report, cache_file)

    except Exception as e:
        logger.warn(f"Error saving cache: {e}. Continue...")

    logger.info("Returning balance sheet report...")
    return {
        "messages": [response],
        "balance_sheet_report": response,
    }


@observe()
async def cash_flow_analyst(
    state: TickerAgentState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """
    This agent node is responsible for analyzing the cash flow of a company.

    Args:
        state (AgentState): The state of the agent
        config (RunnableConfig): The configuration of the agent
    """
    ctx: RequestContext = config.get("configurable", {})["_ctx"]
    ps: PromptService = config.get("configurable", {})["_ps"]
    logger = ctx.logger()
    logger.debug("Starting cash flow analyst...")
    try:
        logger.debug("Checking cache...")
        symbol = state["symbol"]
        assert symbol
        cache_file = report_cache.cache_file_path(symbol, inspect.stack()[0][3])
        report = await report_cache.load_cache(cache_file)
        if report:
            logger.info("Returning data from cache...")
            return {
                "messages": [report["data"]],
                "cash_flow_report": report["data"],
            }

    except Exception as e:
        logger.warn(f"Error loading cache: {e}. Continue...")

    prompt = await ps.get_prompt(
        ctx,
        name=settings.ticker_report_analyze_cash_flow_prompt,
        type="chat",
        label=settings.ticker_report_analyze_cash_flow_label,
    )

    assert "cash_flow" in state
    assert "company_info" in state
    assert "section_7" in state

    chain = prompt.tmpl | prompt.llm_model | StrOutputParser()  # type: ignore

    logger.debug("Calling chain...")
    response = await _invoke_chain(
        chain,
        input_data={
            "cash_flow": state["cash_flow"],
            "industry": state["company_info"]["industry"],
            "section_text": state["section_7"],
        },
    )
    try:
        logger.debug("Saving to cache...")
        report = CachedReport(ts=int(time()), data=response)
        symbol = state["symbol"]
        assert symbol
        cache_file = report_cache.cache_file_path(symbol, inspect.stack()[0][3])
        await report_cache.save_cache(report, cache_file)

    except Exception as e:
        logger.warn(f"Error saving cache: {e}. Continue...")

    logger.info("Returning cash flow report...")
    return {
        "messages": [response],
        "cash_flow_report": response,
    }


@observe()
async def summary_analyst(
    state: TickerAgentState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """
    This agent node is responsible for summarizing the reports of a company.

    Args:
        state (AgentState): The state of the agent
        config (RunnableConfig): The configuration of the agent
    """
    ctx: RequestContext = config.get("configurable", {})["_ctx"]
    ps: PromptService = config.get("configurable", {})["_ps"]
    logger = ctx.logger()
    logger.debug("Starting summary analyst...")
    try:
        logger.debug("Checking cache...")
        symbol = state["symbol"]
        assert symbol
        cache_file = report_cache.cache_file_path(symbol, inspect.stack()[0][3])
        report = await report_cache.load_cache(cache_file)
        if report:
            logger.info("Returning data from cache...")
            return {
                "messages": [report["data"]],
                "summary_report": report["data"],
            }

    except Exception as e:
        logger.warn(f"Error loading cache: {e}. Continue...")

    prompt = await ps.get_prompt(
        ctx,
        name=settings.ticker_report_summarize_report_prompt,
        type="chat",
        label=settings.ticker_report_summarize_report_label,
    )

    assert state["income_stmt_report"]
    assert state["balance_sheet_report"]
    assert state["cash_flow_report"]

    chain = prompt.tmpl | prompt.llm_model | StrOutputParser()  # type: ignore

    logger.debug("Calling chain...")
    response = await _invoke_chain(
        chain,
        input_data={
            "income_stmt_report": state["income_stmt_report"],
            "balance_sheet_report": state["balance_sheet_report"],
            "cash_flow_report": state["cash_flow_report"],
        },
    )
    try:
        logger.debug("Saving to cache...")
        report = CachedReport(ts=int(time()), data=response)
        symbol = state["symbol"]
        assert symbol
        cache_file = report_cache.cache_file_path(symbol, inspect.stack()[0][3])
        await report_cache.save_cache(report, cache_file)

    except Exception as e:
        logger.warn(f"Error saving cache: {e}. Continue...")

    logger.info("Returning summary report...")
    return {
        "messages": [response],
        "summary_report": response,
    }


@observe()
async def company_info(
    state: TickerAgentState,
    config: RunnableConfig,
):
    """
    This agent node is responsible for getting the company information of a company.
    """
    ctx: RequestContext = config.get("configurable", {})["_ctx"]
    fs: FinService = config.get("configurable", {})["_fs"]
    symbol = state["symbol"]
    assert symbol is not None
    logger = ctx.logger()
    logger.debug(f"Getting company info for {symbol}...")
    company_info = await fs.str_get_company_info(symbol)

    logger.info("Returning company info...")
    return {
        "company_info": json.loads(company_info),
    }


@observe()
async def income_stmt(
    state: TickerAgentState,
    config: RunnableConfig,
):
    """
    This agent node is responsible for getting the income statement of a company.
    """
    ctx: RequestContext = config.get("configurable", {})["_ctx"]
    fs: FinService = config.get("configurable", {})["_fs"]
    symbol = state["symbol"]
    assert symbol is not None
    logger = ctx.logger()
    logger.debug(f"Getting income statement for {symbol}...")
    income_stmt = await fs.str_get_income_stmt(symbol)

    logger.info("Returning income statement...")
    return {
        "income_stmt": income_stmt,
    }


@observe()
async def balance_sheet(
    state: TickerAgentState,
    config: RunnableConfig,
):
    """
    This agent node is responsible for getting the balance sheet of a company.
    """
    ctx: RequestContext = config.get("configurable", {})["_ctx"]
    fs: FinService = config.get("configurable", {})["_fs"]
    symbol = state["symbol"]
    assert symbol is not None
    logger = ctx.logger()
    logger.debug(f"Getting balance sheet for {symbol}...")
    balance_sheet = await fs.str_get_balance_sheet(symbol)

    logger.info("Returning balance sheet...")
    return {
        "balance_sheet": balance_sheet,
    }


@observe()
async def cash_flow(
    state: TickerAgentState,
    config: RunnableConfig,
):
    """
    This agent node is responsible for getting the cash flow of a company.
    """
    ctx: RequestContext = config.get("configurable", {})["_ctx"]
    fs: FinService = config.get("configurable", {})["_fs"]
    symbol = state["symbol"]
    assert symbol is not None
    logger = ctx.logger()
    logger.debug(f"Getting cash flow for {symbol}...")
    cash_flow = await fs.str_get_cash_flow(symbol)

    logger.info("Returning cash flow...")
    return {
        "cash_flow": cash_flow,
    }


@observe()
async def section_7(
    state: TickerAgentState,
    config: RunnableConfig,
):
    """
    This agent node is responsible for getting the section 7 of a company.
    """
    ctx: RequestContext = config.get("configurable", {})["_ctx"]
    ss: SecService = config.get("configurable", {})["_ss"]
    sec_api_key: str = config.get("configurable", {})["_sec_api_key"]
    symbol = state["symbol"]
    assert symbol is not None
    logger = ctx.logger()
    logger.debug(f"Getting section 7 for {symbol}...")
    section_7 = await ss.get_section(ctx, symbol, "7", "text", sec_api_key)
    logger.info("Returning section 7...")
    return {
        "section_7": section_7,
    }


@observe()
async def symbol_detection(
    state: TickerAgentState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """
    This agent node is responsible for extracting the ticker symbol of a company.
    """
    ps: PromptService = config.get("configurable", {})["_ps"]
    ctx: RequestContext = config.get("configurable", {})["_ctx"]
    logger = ctx.logger()
    logger.debug("Extracting ticker symbol...")

    prompt = await ps.get_prompt(
        ctx,
        name=settings.ticker_report_symbol_detection_prompt,
        label=settings.ticker_report_symbol_detection_label,
        type="chat",
    )
    chain = prompt.tmpl | prompt.llm_model | StrOutputParser()  # type: ignore

    logger.debug("Calling chain...")
    response = await _invoke_chain(
        chain,
        input_data={
            "user_query": state["user_query"],
        },
    )
    response = response.strip('"').strip("'").strip()

    logger.info(f"Ticker symbol: {response}")
    return {
        "messages": [response],
        "symbol": response,
    }


@observe()
async def show_confirm_action(
    state: TickerAgentState,
    config: RunnableConfig,
) -> Dict[str, Any]:
    ctx: RequestContext = config.get("configurable", {})["_ctx"]
    logger = ctx.logger()
    logger.debug("Waiting for user confirmation...")
    if (
        "symbol" not in state
        or state["symbol"] is None
        or state["symbol"] == ""
        or state["symbol"] == "UNKNOWN"
    ):
        logger.debug("No symbol found, ask for symbol...")
        response = ChatRespDto(
            action=ChatRespAction.SHOW_REPLY,
            response="You can provide a ticker symbol or company name and I will grab the financial report for you!",
            metadata=None,
        )
    elif "symbol" in state and not SupportedTicker.has_value(state["symbol"]):
        response = ChatRespDto(
            action=ChatRespAction.SHOW_REPLY,
            response=f"Sorry, I don't support the ticker symbol {state['symbol']}!",
            metadata=None,
        )
    else:
        response = ChatRespDto(
            action=ChatRespAction.SHOW_TICKER_REPORT,
            response=f"Let's see the financial report of ticker symbol {state['symbol']}!",
            metadata=ChatRespMetadataForShowTickerReport(
                ticker=SupportedTicker(state["symbol"]),
            ),
        )
    return {
        "responses": [response.model_dump_json()],
    }
