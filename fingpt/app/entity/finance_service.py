from typing import Optional, TypedDict

import pandas as _pd
from pydantic import BaseModel


class TickerKeyData(BaseModel):
    six_month_avg_val: Optional[float] = None
    closing_price: Optional[float] = None
    market_cap: Optional[float] = None
    fifty_two_weeks_price_range: Optional[float] = None
    bvps: Optional[float] = None
    volatility_beta: Optional[float] = None
    target_low_price: Optional[float] = None
    target_mean_price: Optional[float] = None
    target_median_price: Optional[float] = None
    target_high_price: Optional[float] = None

    def attribute_to_info_key(self):
        return {
            "closing_price": "previousClose",
            "market_cap": "marketCap",
            "fifty_two_weeks_price_range": "fiftyTwoWeeksPriceRange",
            "bvps": "bookValue",
            "volatility_beta": "beta",
            "target_low_price": "targetLowPrice",
            "target_mean_price": "targetMeanPrice",
            "target_median_price": "targetMedianPrice",
            "target_high_price": "targetHighPrice",
        }


class TickerInfo(BaseModel):
    company_name: Optional[str]
    industry: Optional[str]
    sector: Optional[str]
    country: Optional[str]
    website: Optional[str]
    current_price: Optional[float]
    price_change: Optional[float]
    exchange: Optional[str]
    address1: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    phone: Optional[str]
    business_summary: Optional[str]


class StockData:
    info: dict
    financials: _pd.DataFrame
    balance_sheet: _pd.DataFrame
    cashflow: _pd.DataFrame
    recommendations: _pd.DataFrame
    history_1y: _pd.DataFrame
    history_6m: _pd.DataFrame

    def __init__(
        self,
        info,
        financials,
        balance_sheet,
        cashflow,
        recommendations,
        history_1y,
        history_6m,
    ) -> None:
        self.info = info
        self.financials = financials
        self.balance_sheet = balance_sheet
        self.cashflow = cashflow
        self.recommendations = recommendations
        self.history_1y = history_1y
        self.history_6m = history_6m


class CachedReport(TypedDict):
    ts: int
    data: str
