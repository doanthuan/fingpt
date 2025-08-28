import asyncio
from typing import Any

from app.core.context import RequestContext
from app.entity import RawDataFormat
from app.finance.fin_service import FinService
from app.finance.sec_service import SecService
from app.prompt.prompt_service import PromptService
from app.utils.modified_langfuse_decorator import observe  # type: ignore


class ReportService:
    def __init__(
        self, fin_srv: FinService, sec_srv: SecService, prompt_srv: PromptService
    ) -> None:
        self._fin_srv = fin_srv
        self._sec_srv = sec_srv
        self._prompt_srv = prompt_srv

    @observe()
    async def raw_data_report(
        self,
        *,
        ctx: RequestContext,
        symbol: str,
        sec_api_key: str,
        raw_data_format: RawDataFormat,
    ) -> dict[str, Any]:
        logger = ctx.logger()
        logger.info(f"Get raw data for symbol: {symbol}")
        task1 = self._fin_srv.get_company_info(symbol)
        task2 = self._fin_srv.get_income_stmt(symbol)
        task3 = self._fin_srv.get_balance_sheet(symbol)
        task4 = self._fin_srv.get_cash_flow(symbol)
        task5 = self._fin_srv.analyst_recommendation(ctx, symbol)
        task6 = self._sec_srv.get_section(ctx, symbol, "7", "text", sec_api_key)
        task7 = self._fin_srv.get_home_chart_data(symbol)
        task8 = self._fin_srv.get_sp500_chart_data()
        task9 = self._fin_srv.get_key_data(ctx, symbol)

        (
            info,
            income_stmt,
            balance_sheet,
            cash_flow,
        ) = await asyncio.gather(
            task1,
            task2,
            task3,
            task4,
        )

        (
            analyst_recommendation,
            section_text,
            home_chart_data,
            sp500_chart_data,
            key_data,
        ) = await asyncio.gather(task5, task6, task7, task8, task9)

        result = {
            "company_info": info,
            "analyst_recommendation": (
                analyst_recommendation[0]
                if analyst_recommendation[0] is not None
                else "No data"
            ),
            "section_7_text": section_text,
            "home_chart_data": home_chart_data,
            "sp500_chart_data": sp500_chart_data,
            "key_data": key_data,
        }

        if raw_data_format == RawDataFormat.CSV:
            result["income_stmt"] = (
                income_stmt.to_csv() if not income_stmt.empty else "No data"
            )
            result["balance_sheet"] = (
                balance_sheet.to_csv() if not balance_sheet.empty else "No data"
            )
            result["cash_flow"] = (
                cash_flow.to_csv() if not cash_flow.empty else "No data"
            )

        elif raw_data_format == RawDataFormat.MARKDOWN:
            result["income_stmt"] = (
                income_stmt.to_markdown() if not income_stmt.empty else "No data"
            )
            result["balance_sheet"] = (
                balance_sheet.to_markdown() if not balance_sheet.empty else "No data"
            )
            result["cash_flow"] = (
                cash_flow.to_markdown() if not cash_flow.empty else "No data"
            )

        logger.info("Returning data...")
        return result
