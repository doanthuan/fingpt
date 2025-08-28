from langchain_core.runnables import RunnableConfig
from langchain_openai import AzureChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.assistant.ticker.constant import (
    BALANCE_SHEET_ANALYST_NODE,
    BALANCE_SHEET_NODE,
    CASH_FLOW_ANALYST_NODE,
    CASH_FLOW_NODE,
    COMPANY_INFO_NODE,
    INCOME_STMT_ANALYST_NODE,
    INCOME_STMT_NODE,
    SECTION_7_NODE,
    SUMMARY_ANALYST_NODE,
)
from app.assistant.ticker.state import TickerAgentConfig, TickerAgentState
from app.core.config import settings
from app.core.context import RequestContext
from app.finance.fin_service import FinService
from app.finance.sec_service import SecService
from app.prompt.prompt_service import PromptService
from app.utils.modified_langfuse_decorator import observe  # type: ignore

from .nodes import (
    balance_sheet,
    balance_sheet_analyst,
    cash_flow,
    cash_flow_analyst,
    company_info,
    income_stmt,
    income_stmt_analyst,
    section_7,
    summary_analyst,
)


class TickerAgent:
    def __init__(
        self,
        fin_srv: FinService,
        sec_srv: SecService,
        prompt_srv: PromptService,
    ) -> None:
        self._shared_config = RunnableConfig(
            configurable=dict(
                TickerAgentConfig(
                    _fs=fin_srv,
                    _ss=sec_srv,
                    _ps=prompt_srv,
                    _llm_model=AzureChatOpenAI(
                        azure_deployment=settings.azure_openai_deployment,
                    ),
                    _ctx=None,
                    _sec_api_key=None,
                )
            )
        )
        self.workflow = self._get_workflow()
        self.agent = self.workflow.compile()

    def _get_workflow(
        self,
    ) -> StateGraph:
        workflow = StateGraph(
            state_schema=TickerAgentState,
            config_schema=TickerAgentConfig,
        )

        workflow.add_node(COMPANY_INFO_NODE, company_info)
        workflow.add_node(INCOME_STMT_NODE, income_stmt)
        workflow.add_node(BALANCE_SHEET_NODE, balance_sheet)
        workflow.add_node(CASH_FLOW_NODE, cash_flow)
        workflow.add_node(SECTION_7_NODE, section_7)

        workflow.add_node(INCOME_STMT_ANALYST_NODE, income_stmt_analyst)
        workflow.add_node(BALANCE_SHEET_ANALYST_NODE, balance_sheet_analyst)
        workflow.add_node(CASH_FLOW_ANALYST_NODE, cash_flow_analyst)
        workflow.add_node(SUMMARY_ANALYST_NODE, summary_analyst)

        workflow.add_edge(START, COMPANY_INFO_NODE)
        workflow.add_edge(START, INCOME_STMT_NODE)
        workflow.add_edge(START, BALANCE_SHEET_NODE)
        workflow.add_edge(START, CASH_FLOW_NODE)
        workflow.add_edge(START, SECTION_7_NODE)

        workflow.add_edge(COMPANY_INFO_NODE, INCOME_STMT_ANALYST_NODE)
        workflow.add_edge(COMPANY_INFO_NODE, BALANCE_SHEET_ANALYST_NODE)
        workflow.add_edge(COMPANY_INFO_NODE, CASH_FLOW_ANALYST_NODE)

        workflow.add_edge(SECTION_7_NODE, INCOME_STMT_ANALYST_NODE)
        workflow.add_edge(SECTION_7_NODE, BALANCE_SHEET_ANALYST_NODE)
        workflow.add_edge(SECTION_7_NODE, CASH_FLOW_ANALYST_NODE)

        workflow.add_edge(INCOME_STMT_NODE, INCOME_STMT_ANALYST_NODE)
        workflow.add_edge(BALANCE_SHEET_NODE, BALANCE_SHEET_ANALYST_NODE)
        workflow.add_edge(CASH_FLOW_NODE, CASH_FLOW_ANALYST_NODE)

        workflow.add_edge(INCOME_STMT_ANALYST_NODE, SUMMARY_ANALYST_NODE)
        workflow.add_edge(BALANCE_SHEET_ANALYST_NODE, SUMMARY_ANALYST_NODE)
        workflow.add_edge(CASH_FLOW_ANALYST_NODE, SUMMARY_ANALYST_NODE)

        workflow.add_edge(SUMMARY_ANALYST_NODE, END)

        return workflow

    @observe()
    async def ticker_report(
        self,
        *,
        ctx: RequestContext,
        symbol: str,
        sec_api_key: str,
    ) -> dict[str, str]:
        logger = ctx.logger()
        logger.info(f"Starting financial report for symbol: {symbol}")

        cfg = self._shared_config.copy()
        cfg["configurable"]["_ctx"] = ctx
        cfg["configurable"]["_sec_api_key"] = sec_api_key

        logger.info("Invoking workflow...")
        summary = await self.agent.ainvoke(
            {
                "symbol": symbol,
            },
            config=cfg,
            stream_mode="values",
        )

        logger.info("Returning summary response...")

        return {
            "symbol": symbol,
            "summary": summary["summary_report"],
            "income_stmt_report": summary["income_stmt_report"],
            "balance_sheet_report": summary["balance_sheet_report"],
            "cash_flow_report": summary["cash_flow_report"],
        }
