import asyncio
import os
import re
import uuid
from typing import Dict, Tuple
from uuid import uuid4

from httpx import AsyncClient

from app.core import Logger
from app.entity import ChatReqAction, ChatReqDto, ChatReqMetadataForQuery
from app.utils.misc import read_yaml
from integration_tests.assert_methods import call_assert_method
from integration_tests.entities import (
    APIConfig,
    AssertMethods,
    LoginAPIInfo,
    TestCase,
    TestCases,
)
from integration_tests.exceptions import TestException


def _cookies_to_dict(cookies: str) -> Dict[str, str] | None:
    if cookies is None:
        return cookies
    return {
        c.split("=")[0].strip(): c.split("=")[1].strip() for c in cookies.split("; ")
    }


async def _local_login(
    client: AsyncClient, login_info: LoginAPIInfo
) -> Tuple[str, str]:
    password = os.getenv(login_info.input_password_env)
    response = await client.post(
        login_info.api_url,
        json={
            "username": login_info.input_username,
            "password": password,
            "user_type": login_info.user_type,
        },
    )
    response_json = response.json()
    access_token = response_json[login_info.access_token_field]
    cookie = response_json[login_info.cookie_field]
    return access_token, cookie


def _extract_prev_output_data(key: str, responses: list[dict]) -> dict:
    parts = key.split(".")
    if len(parts) == 1:
        assert "steps" in parts[0]
        step_index = eval(parts[0].replace("steps", ""))[0]
        return responses[step_index]
    assert "steps" in parts[0]
    step_index = eval(parts[0].replace("steps", ""))[0]
    current = responses[step_index]
    parts = parts[1:]
    for p in parts:
        if "[" in p and "]" in p:
            key_name, idx = re.match(r"(.+?)\[(\d+)]", p).groups()
            current = current.get(key_name)[int(idx)]
        else:
            current = current.get(p)
    return current


def _compile_input(test_input: dict, responses: list[dict], test_id: str) -> dict:
    compiled_input = {}
    for key, value in test_input.items():
        if value == "random":
            compiled_input[key] = test_id

        elif isinstance(value, str) and value.startswith("$"):
            response_key = value[2:-1] if value[1] == "{" else value[1:]
            prev_output_data = _extract_prev_output_data(response_key, responses)
            compiled_input[key] = prev_output_data
        elif isinstance(value, dict):
            compiled_input[key] = _compile_input(value, responses, test_id)
        else:
            compiled_input[key] = value

    return compiled_input


async def _get(
    client: AsyncClient,
    api_config: APIConfig,
    header: Dict[str, str],
    testcase: TestCase,
    logger: Logger,
    **kwargs,
):
    logger.debug(f"Test GET for {api_config.name} with testcase {testcase.name}....")
    try:
        test_id = str(uuid4())
        responses = []
        for step in testcase.steps:
            compiled_input = _compile_input(step.input, responses, test_id)
            compiled_output = _compile_input(step.output.response, responses, test_id)
            response = await client.get(
                api_config.api_url, headers=header, params=compiled_input, **kwargs
            )
            responses.append(response.json())
            assert (
                response.status_code == step.output.status
            ), f"Expected {step.output.status}, got {response.status_code}"
            assert call_assert_method(
                step.assert_method, response.json(), compiled_output
            ), f"Assertion failed for {step.name}"
        logger.debug(
            f"===> Test GET for {api_config.name} with testcase {testcase.name} passed"
        )
    except Exception as e:
        raise TestException(
            f"Test GET for {api_config.name} - {testcase.name} failed: {e}"
        )


async def _post(
    client: AsyncClient,
    api_config: APIConfig,
    header: Dict[str, str],
    testcase: TestCase,
    logger: Logger,
    **kwargs,
):
    logger.debug(f"Test POST for {api_config.name} with testcase {testcase.name}....")
    responses = []
    try:
        test_id = str(uuid4())
        for step in testcase.steps:
            # compile input and previous output data
            compiled_input = _compile_input(step.input, responses, test_id)
            compiled_output = _compile_input(step.output.response, responses, test_id)
            response = await client.post(
                api_config.api_url, headers=header, json=compiled_input, **kwargs
            )
            # store response for future steps
            assert (
                response.status_code == step.output.status
            ), f"Expected {step.output.status}, got {response.status_code}"
            if step.assert_method != AssertMethods.LLM_FLEXIBLE:
                assert call_assert_method(
                    step.assert_method, response.json(), compiled_output
                ), f"Assertion failed for {step.name}"
            else:
                counter = 0
                additional_input = step.additional_assert_input
                while True:
                    additional_input.reply_count = counter
                    assert_result = call_assert_method(
                        step.assert_method,
                        response.json(),
                        compiled_output,
                        additional_input,
                    )
                    if isinstance(assert_result, bool):
                        assert (
                            assert_result
                        ), f"Assertion failed for {step.name}. Last response {response.json()}"
                        break
                    else:
                        new_input = ChatReqDto(
                            action=ChatReqAction.QUERY,
                            metadata=ChatReqMetadataForQuery(
                                thread_id=test_id,
                                user_query=assert_result,
                            ),
                        )
                        response = await client.post(
                            api_config.api_url,
                            headers=header,
                            json=new_input.model_dump(),
                            **kwargs,
                        )

                    counter += 1
            responses.append(response.json())

        logger.debug(
            f"===> Test POST for {api_config.name} with testcase {testcase.name} passed"
        )
    except Exception as e:
        raise TestException(
            f"Test POST for {api_config.name} - {testcase.name} failed: {e}. List of resposne {responses}"
        )


async def local_test_get(
    client: AsyncClient, api_config: APIConfig, login_info: LoginAPIInfo = None
):
    request_id = str(uuid.uuid4())
    logger = Logger(request_id)
    header = {"request-id": request_id}
    cookie = None
    if api_config.login_required:
        if login_info is None:
            raise ValueError("Login info is required for this API")
        access_token, cookie = await _local_login(client, login_info)
        header["Authorization"] = f"Bearer {access_token}"
    testcases = read_yaml(TestCases, api_config.testcases_path)
    for batch in range(0, len(testcases.testcases), api_config.batch_size):
        tasks = []
        for testcase in testcases.testcases[batch : batch + api_config.batch_size]:
            # make request to the API
            # compare the response with the expected output
            tasks.append(
                _get(
                    client,
                    api_config,
                    header,
                    testcase,
                    logger,
                    cookies=_cookies_to_dict(cookie),
                )
            )
        async with asyncio.timeout(api_config.timeout):
            results = await asyncio.gather(*tasks)
            for r in results:
                if isinstance(r, Exception):
                    raise r


async def local_test_post(
    client: AsyncClient, api_config: APIConfig, login_info: LoginAPIInfo = None
):
    request_id = str(uuid.uuid4())
    logger = Logger(request_id)
    header = {"request-id": request_id}
    cookie = None
    if api_config.login_required:
        if login_info is None:
            raise ValueError("Login info is required for this API")
        access_token, cookie = await _local_login(client, login_info)
        header["Authorization"] = f"Bearer {access_token}"
    testcases = read_yaml(TestCases, api_config.testcases_path)
    for batch in range(0, len(testcases.testcases), api_config.batch_size):
        tasks = []
        for testcase in testcases.testcases[batch : batch + api_config.batch_size]:
            # make request to the API
            # compare the response with the expected output
            tasks.append(
                _post(
                    client,
                    api_config,
                    header,
                    testcase,
                    logger,
                    cookies=_cookies_to_dict(cookie),
                )
            )
        async with asyncio.timeout(api_config.timeout):
            results = await asyncio.gather(*tasks)
            for r in results:
                if isinstance(r, Exception):
                    raise r
