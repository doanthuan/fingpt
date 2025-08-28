import os
import pickle
import shutil
from pathlib import Path

import pytest
from sec_api import ExtractorApi

from app.assistant.constant import CONFIGURABLE_CONTEXT_KEY, CONTEXT_KEY
from app.finance.sec_service import SecService

FAKE_TOKEN = "fake_api_key"
FAKE_URL = "https://api.sec-api.io/fake_url"


def _sec_mock_data() -> str:
    mock_data_dir = Path("app/finance/mock_data")
    mock_file = mock_data_dir / "AAPL_7.pkl"
    with open(mock_file, "rb") as f:
        data = f.read()
        loaded_data = pickle.loads(data)
        return loaded_data


@pytest.fixture()
def sec_service_mocker(mocker, mock_aioresponse):
    # override the cache directory for testing
    tmp_dir = Path(".tmp")
    mocker.patch(
        # "app.finance.sec_service.CACHE_DIR",
        "app.utils.cache_manager.CACHE_DIR",
        str(tmp_dir / "cache_dir"),
    )
    mock_aioresponse.post(
        f"https://api.sec-api.io?token={FAKE_TOKEN}",
        payload={
            "filings": [{"linkToFilingDetails": FAKE_URL}],
        },
    )
    # get mock data for
    mocker.patch.object(ExtractorApi, "get_section", return_value=_sec_mock_data())
    yield
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


# TODO An Pham Fix this later
# @pytest.mark.asyncio
# async def test_get_10k_filing(mocker, sec_service_mocker, agent_config):
#     service = SecService()
#     ctx = agent_config[CONFIGURABLE_CONTEXT_KEY][CONTEXT_KEY]
#     mocker.patch("app.finance.sec_service.ALLOWED_SEC_API_CALLS", "true")
#     # at the first call, the cache is empty, we get the URL from the API
#     url = await service.get_10k_filing(ctx, "AAPL", "fake_api_key")
#     assert url == FAKE_URL
#     # at the second call, the cache is not empty, we get the URL from the cache
#     # Reset ALLOWED_SEC_API_CALLS to false and make sure the cache is used without any exception
#     mocker.patch("app.finance.sec_service.ALLOWED_SEC_API_CALLS", "false")
#     url = await service.get_10k_filing(ctx, "AAPL", "fake_api_key")
#     assert url == FAKE_URL


# @pytest.mark.asyncio
# async def test_get_10k_filing_failed(mocker, sec_service_mocker, agent_config):
#     service = SecService()
#     ctx = agent_config[CONFIGURABLE_CONTEXT_KEY][CONTEXT_KEY]
#     # disable ALLOWED_SEC_API_CALLS
#     mocker.patch("app.finance.sec_service.ALLOWED_SEC_API_CALLS", "false")
#     with pytest.raises(Exception):
#         await service.get_10k_filing(ctx, "AAPL", "fake_api_key")


@pytest.mark.asyncio
async def test_get_section(mocker, sec_service_mocker, agent_config):
    service = SecService()
    ctx = agent_config[CONFIGURABLE_CONTEXT_KEY][CONTEXT_KEY]
    mocker.patch("app.finance.sec_service.ALLOWED_SEC_API_CALLS", "true")
    section = await service.get_section(ctx, "AAPL", "7", "text", "fake_api_key")
    assert section == _sec_mock_data().decode("utf-8")
    # at the second call, the cache is not empty, we get the section from the cache
    # Reset ALLOWED_SEC_API_CALLS to false and make sure the cache is used without any exception
    mocker.patch("app.finance.sec_service.ALLOWED_SEC_API_CALLS", "false")
    section = await service.get_section(ctx, "AAPL", "7", "text", "fake_api_key")
    assert section == _sec_mock_data().decode("utf-8")
