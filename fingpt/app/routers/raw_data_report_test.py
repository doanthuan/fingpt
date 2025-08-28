from unittest.mock import PropertyMock

from yfinance import Ticker

from app.routers.raw_data_report import yfinance_checker


def test_yfinance_checker(mocker):
    mocker.patch.object(
        Ticker,
        "info",
        side_effect=[{"currency": "USD"}, {}],
        new_callable=PropertyMock,
    )
    status = yfinance_checker()
    call_again = yfinance_checker()
    assert status is True
    assert call_again is True
    yfinance_checker.cache_clear()


def test_yfinance_checker_false(mocker):
    mocker.patch.object(
        Ticker,
        "info",
        side_effect=[
            {},
            {"currency": "USD"},
        ],
        new_callable=PropertyMock,
    )
    status = yfinance_checker()
    call_again = yfinance_checker()
    assert status is False
    assert call_again is False
    yfinance_checker.cache_clear()
