import asyncio
import traceback

from fastapi import HTTPException

from app.assistant import TickerAgent
from app.core.context import RequestContext
from app.entity import RawDataReqDto
from app.ticker.report_service import ReportService
from app.utils.modified_langfuse_decorator import (  # type: ignore
    langfuse_context,
    observe,
)


class TickerController:
    def __init__(
        self,
        report_srv: ReportService,
        ticker_agent: TickerAgent,
    ):
        self.report_srv = report_srv
        self.ticker_agent = ticker_agent

    @observe(name="Generate Ticker Raw Report Controller")
    async def raw_data_report(
        self,
        ctx: RequestContext,
        headers: dict[str, str],
        req: RawDataReqDto,
    ):
        logger = ctx.logger()
        langfuse_context.update_current_trace(
            session_id=ctx.request_id(),
        )
        logger.info(f"Generating raw data report for symbol: {req.symbol}")
        try:
            task1 = self.report_srv.raw_data_report(
                ctx=ctx,
                symbol=req.symbol.value,
                sec_api_key=headers["sec-api-key"],
                raw_data_format=req.raw_data_format,
            )
            task2 = self.ticker_agent.ticker_report(
                ctx=ctx, symbol=req.symbol.value, sec_api_key=headers["sec-api-key"]
            )
            result, report_summary = await asyncio.gather(task1, task2)
            result.update(report_summary)
            return result

        except Exception as e:
            logger.error(f"Error getting raw data report: {str(e)}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail="Internal server error: " + str(e),
            )
        finally:
            logger.info("Controller exiting...")
