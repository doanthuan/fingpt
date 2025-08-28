import time
import uuid
from functools import lru_cache
from typing import Annotated

import yfinance as yf
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header

from app.container import ServerContainer
from app.core import RequestContext
from app.entity import RawDataReqDto
from app.finance.fin_service import FinService
from app.ticker.ticker_controller import TickerController
from app.utils.modified_langfuse_decorator import observe

raw_data_router = APIRouter()


@observe()
@raw_data_router.post(
    "/v1/reports/ticker/raw",
    summary="Return Raw Ticker Data",
    response_description="The raw data collected for a ticker symbol",
)
@inject
async def raw_data_report(
    req: RawDataReqDto,
    ticker_ctrl: TickerController = Depends(
        Provide[ServerContainer.ticker_module().ticker_ctrl],
    ),
    x_request_id: Annotated[str, Header()] = str(uuid.uuid4()),
    x_sec_api_key: Annotated[str, Header()] = "SEC_API_KEY",
):
    """
    Return raw data for a specified ticker symbol.

    This endpoint accepts a ticker symbol and processes it to return raw data.

    Headers:
    - x-request-id (str): (OPTIONAL) The request ID.
    - x-sec-api-key (str): (OPTIONAL) The API key for the financial data provider.

    Args:
    - symbol (SupportedTicker): The ticker symbol to return raw data for.
    - raw_data_format (RawDataFormat): The format of the raw data to return.

    Returns:
    - JSON response containing the raw data collected for the ticker symbol or an error message.
    """
    ctx = RequestContext(x_request_id)
    logger = ctx.logger()
    logger.info(f"Received request for sympol: {req.symbol}")
    headers = {
        "sec-api-key": x_sec_api_key,
    }
    logger.debug(f"Headers: {headers}")
    return await ticker_ctrl.raw_data_report(ctx=ctx, headers=headers, req=req)


@raw_data_router.post("/v1/reports/ticker/cache", summary="Cache all ticker data")
@inject
async def cache_all_ticker():
    fin_srv = FinService()
    await fin_srv.cache_all_ticker()


def _get_ttl_hash():
    return round(time.time() / 60 * 5)


@lru_cache()
def yfinance_checker(ttl_hash=_get_ttl_hash()):
    del ttl_hash
    ticker = yf.Ticker("AAPL")
    if ticker and ticker.info:
        return True
    return False
