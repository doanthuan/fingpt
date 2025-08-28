import asyncio
from datetime import datetime
from typing import Any, List

import pandas
import yfinance as yf  # type: ignore
from aiocache import cached
from aiocache.serializers import PickleSerializer
from pandas import DataFrame
from tenacity import retry, stop_after_attempt, stop_after_delay, wait_random
from yfinance.ticker import Ticker  # type: ignore

from app.core.context import RequestContext
from app.entity.api import SupportedTicker
from app.entity.finance_service import StockData, TickerInfo, TickerKeyData
from app.finance.constant import SYMBOL_SP_500
from app.utils.cache_manager import stock_cache


class FinService:
    def __init__(
        self,
    ) -> None:
        self.stock_data: dict[str, Any] = {}
        self._stock_cache = stock_cache

    @retry(
        reraise=True,
        stop=(stop_after_delay(60) | stop_after_attempt(3)),
        wait=wait_random(min=1, max=5),
    )
    async def get_stock_data(
        self,
        symbol: str,
        force_cache: bool = False,
    ) -> StockData:
        cache_file = self._stock_cache.cache_file_path(symbol, "ticker")
        stock_data = await self._stock_cache.load_cache(cache_file)
        if force_cache or stock_data is None:
            ticker = await asyncio.to_thread(self._fetch_stock_data, symbol)

            now = datetime.now()
            last_year = datetime(year=now.year - 1, month=now.month, day=now.day)
            history_1y = ticker.history(
                start=last_year.strftime("%Y-%m-%d"),
                end=now.strftime("%Y-%m-%d"),
                interval="1d",
            )
            history_6m = ticker.history(period="6mo")

            stock_data = StockData(
                info=ticker.info,
                financials=ticker.financials,
                balance_sheet=ticker.balance_sheet,
                cashflow=ticker.cashflow,
                recommendations=ticker.recommendations,  # type: ignore
                history_1y=history_1y,
                history_6m=history_6m,
            )
            await self._stock_cache.save_cache(stock_data, cache_file)
        return stock_data

    def _fetch_stock_data(self, symbol: str) -> Ticker:
        return yf.Ticker(symbol)

    @cached(ttl=10, serializer=PickleSerializer())
    async def get_company_info(
        self,
        symbol: str,
    ) -> TickerInfo:
        """Call this to get company info for a ticker symbol"""
        info = (await self.get_stock_data(symbol)).info

        return TickerInfo(
            company_name=info.get("shortName"),
            industry=info.get("industry"),
            sector=info.get("sector"),
            country=info.get("country"),
            website=info.get("website"),
            current_price=info.get("currentPrice"),
            price_change=float(
                "{:.2f}".format(info.get("currentPrice", 0) - info.get("open", 0))
            ),
            exchange=info.get("exchange"),
            address1=info.get("address1"),
            city=info.get("city"),
            state=info.get("state"),
            zip=info.get("zip"),
            phone=info.get("phone"),
            business_summary=info.get("longBusinessSummary"),
        )

    async def str_get_company_info(
        self,
        symbol: str,
    ) -> str:
        """Specialized version that returns a string to be used as agent tool"""
        info = await self.get_company_info(symbol)
        return info.model_dump_json()

    @cached(ttl=3600, serializer=PickleSerializer())
    async def get_income_stmt(
        self,
        symbol: str,
    ):
        return (await self.get_stock_data(symbol)).financials

    async def str_get_income_stmt(
        self,
        symbol: str,
    ):
        """Specialized version that returns a string to be used as agent tool"""
        income_stmt = await self.get_income_stmt(symbol)
        return income_stmt.to_markdown()

    @cached(ttl=3600, serializer=PickleSerializer())
    async def get_balance_sheet(
        self,
        symbol: str,
    ):
        return (await self.get_stock_data(symbol)).balance_sheet

    async def str_get_balance_sheet(
        self,
        symbol: str,
    ) -> str:
        sheet = await self.get_balance_sheet(symbol)
        return sheet.to_markdown()

    @cached(ttl=3600, serializer=PickleSerializer())
    async def get_cash_flow(
        self,
        symbol: str,
    ):
        return (await self.get_stock_data(symbol)).cashflow

    async def str_get_cash_flow(
        self,
        symbol: str,
    ):
        flow = await self.get_cash_flow(symbol)
        return flow.to_markdown()

    @cached(ttl=3600, serializer=PickleSerializer())
    async def _get_analyst_recommendation(self, symbol: str):
        recommendations = (await self.get_stock_data(symbol)).recommendations
        row_0 = recommendations.iloc[0, 1:]  # Exclude 'period' column
        max_votes = row_0.max()  # Find the maximum voting result
        majority_voting_result = row_0[row_0 == max_votes].index.tolist()
        return majority_voting_result[0], max_votes

    async def analyst_recommendation(
        self,
        ctx: RequestContext,
        symbol: str,
    ):
        try:
            majority_voting_result, max_votes = await self._get_analyst_recommendation(
                symbol
            )
        except Exception as e:
            ctx.logger().error(f"Error getting analyst recommendation: {e}")
            return None, None
        return majority_voting_result, max_votes

    async def str_analyst_recommendation(
        self,
        ctx: RequestContext,
        symbol: str,
    ) -> str:
        recommendation = await self.analyst_recommendation(ctx, symbol)
        return str(recommendation[0] if recommendation else "No data")

    @cached(ttl=3600, serializer=PickleSerializer())
    async def _get_key_data(self, symbol: str):
        ticker_key_data = TickerKeyData()
        ticker = await self.get_stock_data(symbol)
        six_month_price: DataFrame = ticker.history_6m
        if not six_month_price.empty and len(six_month_price):
            six_month_average_volume = round(six_month_price["Volume"].mean() / 1e6, 2)
            ticker_key_data.six_month_avg_val = six_month_average_volume
        if "marketCap" in ticker.info:
            setattr(
                ticker_key_data,
                "market_cap",
                round(ticker.info["marketCap"] / 1e6, 2),
            )
        if "fiftyTwoWeekLow" in ticker.info and "fiftyTwoWeekHigh" in ticker.info:
            setattr(
                ticker_key_data,
                "fifty_two_weeks_price_range",
                round(
                    ticker.info["fiftyTwoWeekLow"] - ticker.info["fiftyTwoWeekHigh"],
                    2,
                ),
            )
        for key in ticker_key_data.model_dump().keys():
            info_key = ticker_key_data.attribute_to_info_key().get(key)
            if (
                info_key is not None
                and info_key in ticker.info
                and key
                not in (
                    "market_cap",
                    "fifty_two_weeks_price_range",
                    "six_month_avg_val",
                )
            ):
                setattr(ticker_key_data, key, ticker.info.get(info_key))
        return ticker_key_data

    async def get_key_data(self, ctx: RequestContext, symbol: str) -> TickerKeyData:
        ticker_key_data = TickerKeyData()
        try:
            ticker_key_data = await self._get_key_data(symbol)
        except Exception as e:
            logger = ctx.logger()
            logger.error(f"Error getting key data: {e}")
        return ticker_key_data

    @cached(ttl=3600, serializer=PickleSerializer())
    async def get_home_chart_data(
        self,
        symbol: str,
    ) -> List[dict]:

        ticker = await self.get_stock_data(symbol)
        return self.get_chart_data(ticker)

    @cached(ttl=3600, serializer=PickleSerializer())
    async def get_sp500_chart_data(
        self,
    ) -> List[dict]:

        ticker = await self.get_stock_data(SYMBOL_SP_500)
        return self.get_chart_data(ticker)

    def get_chart_data(self, ticker: StockData):
        try:
            history: pandas.DataFrame = ticker.history_1y
        except Exception as e:
            print(f"Error getting chart data: {e}")
            return []
        if history.empty:
            return []
        result = history.reset_index()
        result["Date"] = result["Date"].dt.strftime("%Y-%m-%d")
        result = result.to_dict(orient="records")
        return result

    async def cache_all_ticker(self):
        for ticker in list(SupportedTicker):
            await self.get_stock_data(symbol=ticker.value, force_cache=True)
