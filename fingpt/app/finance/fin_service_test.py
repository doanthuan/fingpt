import os
import pickle
import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest
import yfinance

from app.entity.finance_service import StockData, TickerKeyData
from app.finance.fin_service import FinService
from app.utils.cache_manager import CACHE_DIR, CacheManager


@pytest.fixture()
def mock_ticker(mocker):
    data_dir = Path(__file__).parent.resolve() / "mock_data"
    info_file = data_dir / "msft_data.pkl"
    history_file = data_dir / "6_month_data.parquet"
    with open(info_file, "rb") as f:
        info = pickle.load(f)
    history_data = pd.read_parquet(history_file)
    mocker.patch.object(
        yfinance.Ticker, "info", new_callable=mock.PropertyMock, return_value=info
    )
    mocker.patch.object(yfinance.Ticker, "history", return_value=history_data)


@pytest.mark.asyncio
async def test_get_key_data(mock_ticker):
    expected_key_data = TickerKeyData(
        six_month_avg_val=19.5,
        closing_price=414.71,
        market_cap=3102996.69,
        fifty_two_weeks_price_range=-143.96,
        bvps=36.115,
        volatility_beta=0.896,
        target_low_price=440.0,
        target_mean_price=496.3,
        target_median_price=500.0,
        target_high_price=600.0,
    )
    service = FinService()
    actual_key_data = await service.get_key_data(None, "MSFT")
    assert actual_key_data == expected_key_data


@pytest.mark.asyncio
async def test_get_key_data_missing(mocker):
    data_dir = Path(__file__).parent.resolve() / "mock_data"
    info_file = data_dir / "msft_data.pkl"
    history_file = data_dir / "6_month_data.parquet"
    with open(info_file, "rb") as f:
        info = pickle.load(f)
        del info["targetLowPrice"]
    history_data = pd.read_parquet(history_file)
    mocker.patch.object(
        yfinance.Ticker, "info", new_callable=mock.PropertyMock, return_value=info
    )
    mocker.patch.object(yfinance.Ticker, "history", return_value=history_data)
    expected_key_data = TickerKeyData(
        six_month_avg_val=19.5,
        closing_price=414.71,
        market_cap=3102996.69,
        fifty_two_weeks_price_range=-143.96,
        bvps=36.115,
        volatility_beta=0.896,
        target_low_price=440.0,
        target_mean_price=496.3,
        target_median_price=500.0,
        target_high_price=600.0,
    )
    service = FinService()
    actual_key_data = await service.get_key_data(None, "MSFT")
    assert actual_key_data == expected_key_data


class TestGetStockData(unittest.TestCase):
    def setUp(self):
        # Mock the CacheManager
        self.mock_cache_manager = Mock(spec=CacheManager)
        self.mock_cache_manager.load_cache = AsyncMock()
        self.mock_cache_manager.save_cache = AsyncMock()
        self.mock_cache_manager.cache_file_path = Mock(return_value="mock/path")

        # Create a patcher for the global stock_cache
        self.stock_cache_patcher = patch(
            "app.utils.cache_manager.stock_cache", self.mock_cache_manager
        )
        self.stock_cache_patcher.start()

        # Create FinService instance
        self.fin_service = FinService()

    def tearDown(self):
        self.stock_cache_patcher.stop()

    def create_mock_ticker(self):
        mock_ticker = Mock()
        mock_ticker.info = {"symbol": "AAPL", "name": "Apple Inc"}
        mock_ticker.financials = pd.DataFrame({"col1": [1, 2]})
        mock_ticker.balance_sheet = pd.DataFrame({"col2": [3, 4]})
        mock_ticker.cashflow = pd.DataFrame({"col3": [5, 6]})
        mock_ticker.recommendations = pd.DataFrame({"col4": [7, 8]})
        mock_ticker.history = Mock(return_value=pd.DataFrame({"col5": [9, 10]}))
        return mock_ticker

    @patch("app.finance.fin_service.FinService._fetch_stock_data")
    async def test_get_stock_data_from_cache(self, mock_fetch_stock_data):
        # Arrange
        mock_cached_data = StockData(
            info={"cached": True},
            financials=pd.DataFrame(),
            balance_sheet=pd.DataFrame(),
            cashflow=pd.DataFrame(),
            recommendations=pd.DataFrame(),
            history_1y=pd.DataFrame(),
            history_6m=pd.DataFrame(),
        )
        self.mock_cache_manager.load_cache.return_value = mock_cached_data

        # Act
        result = await self.fin_service.get_stock_data("AAPL")

        # Assert
        self.assertEqual(result, mock_cached_data)
        mock_fetch_stock_data.assert_not_called()
        self.mock_cache_manager.save_cache.assert_not_called()
        self.mock_cache_manager.cache_file_path.assert_called_once_with(
            "AAPL", "ticker"
        )

    @patch("app.finance.fin_service.FinService._fetch_stock_data")
    async def test_get_stock_data_fetch_new(self, mock_fetch_stock_data):
        # Arrange
        self.mock_cache_manager.load_cache.return_value = None
        mock_ticker = self.create_mock_ticker()
        mock_fetch_stock_data.return_value = mock_ticker

        # Act
        result = await self.fin_service.get_stock_data("AAPL")

        # Assert
        self.assertIsInstance(result, StockData)
        self.assertEqual(result.info, mock_ticker.info)
        mock_fetch_stock_data.assert_called_once_with("AAPL")
        self.mock_cache_manager.save_cache.assert_called_once()

    @patch("app.finance.fin_service.FinService._fetch_stock_data")
    async def test_get_stock_data_force_cache(self, mock_fetch_stock_data):
        # Arrange
        mock_cached_data = StockData(
            info={"cached": True},
            financials=pd.DataFrame(),
            balance_sheet=pd.DataFrame(),
            cashflow=pd.DataFrame(),
            recommendations=pd.DataFrame(),
            history_1y=pd.DataFrame(),
            history_6m=pd.DataFrame(),
        )
        self.mock_cache_manager.load_cache.return_value = mock_cached_data
        mock_ticker = self.create_mock_ticker()
        mock_fetch_stock_data.return_value = mock_ticker

        # Act
        result = await self.fin_service.get_stock_data("AAPL", force_cache=True)

        # Assert
        self.assertIsInstance(result, StockData)
        self.assertEqual(result.info, mock_ticker.info)
        mock_fetch_stock_data.assert_called_once_with("AAPL")
        self.mock_cache_manager.save_cache.assert_called_once()


class TestCacheManager(unittest.TestCase):
    def setUp(self):
        self.cache_manager = CacheManager[StockData]()
        self.test_symbol = "TEST"
        self.test_kind = "ticker"

    def test_cache_file_path(self):
        expected_path = os.path.join(
            CACHE_DIR, f"{self.test_symbol}_{self.test_kind}.pkl"
        )
        actual_path = self.cache_manager.cache_file_path(
            self.test_symbol, self.test_kind
        )
        self.assertEqual(actual_path, expected_path)

    @patch("aiofiles.open")
    async def test_load_cache_existing_file(self, mock_open):
        mock_data = StockData(
            info={},
            financials=pd.DataFrame(),
            balance_sheet=pd.DataFrame(),
            cashflow=pd.DataFrame(),
            recommendations=pd.DataFrame(),
            history_1y=pd.DataFrame(),
            history_6m=pd.DataFrame(),
        )
        mock_file = AsyncMock()
        mock_file.read = AsyncMock(return_value=pickle.dumps(mock_data))
        mock_open.return_value.__aenter__.return_value = mock_file

        with patch("os.path.exists", return_value=True):
            result = await self.cache_manager.load_cache("test_path")

        self.assertIsInstance(result, StockData)

    async def test_load_cache_non_existing_file(self):
        with patch("os.path.exists", return_value=False):
            result = await self.cache_manager.load_cache("test_path")

        self.assertIsNone(result)

    def test_memory_cache(self):
        test_data = StockData(
            info={},
            financials=pd.DataFrame(),
            balance_sheet=pd.DataFrame(),
            cashflow=pd.DataFrame(),
            recommendations=pd.DataFrame(),
            history_1y=pd.DataFrame(),
            history_6m=pd.DataFrame(),
        )

        # Test saving to memory
        self.cache_manager.save_memory("test_key", test_data)

        # Test loading from memory
        loaded_data = self.cache_manager.load_memory("test_key")
        self.assertEqual(loaded_data, test_data)

        # Test loading non-existent key
        non_existent = self.cache_manager.load_memory("non_existent")
        self.assertIsNone(non_existent)
