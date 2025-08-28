"""
Integration tests for the server
"""

import asyncio
import os
import sys
import traceback
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from app.server import app
from app.utils.misc import read_yaml
from integration_tests.entities import IntegrationTestConfig
from integration_tests.local_helpers import local_test_get, local_test_post

ROOT_PATH = Path(__file__).parent.resolve()
TEST_CONFIG_PATH = ROOT_PATH / "config.yml"


async def local_runner(test_config: IntegrationTestConfig):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test"
    ) as client:
        tasks = []
        for api_config in test_config.configs:
            if api_config.method == "GET":
                tasks.append(local_test_get(client, api_config, test_config.login_api))
            elif api_config.method == "POST":
                tasks.append(local_test_post(client, api_config, test_config.login_api))
            else:
                raise NotImplementedError(f"Method {api_config.method} not implemented")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                raise result


async def remote_runner(host: str, port: str, test_config: IntegrationTestConfig):
    pass


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 2:
        print("Usage: server_test.py <host> <port>")
        sys.exit(1)

    host = args[0]
    port = args[1]
    # load config from config file to pydantic entity
    # and pass it to the test function
    config: IntegrationTestConfig = read_yaml(
        IntegrationTestConfig, str(TEST_CONFIG_PATH)
    )
    try:
        if host in ("localhost", "127.0.0.1", "0.0.0.0"):
            asyncio.run(local_runner(config))
        else:
            asyncio.run(remote_runner(host, port, config))
    except Exception as e:
        traceback.print_exc()
        print(f"Test failed with error: {e}")
        os._exit(1)
    os._exit(0)
