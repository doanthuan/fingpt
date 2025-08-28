import os
import shutil
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import sentry_sdk
from aioresponses import aioresponses
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langfuse.model import ChatMessageDict
from nemoguardrails import LLMRails
from starlette.requests import Request

from app.assistant.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    EBP_ACCESS_TOKEN_KEY,
    EBP_COOKIE_KEY,
    EBP_EDGE_DOMAIN_KEY,
    LLM_MODEL_KEY,
    PROMPT_SERVICE_KEY,
    THREAD_ID_KEY,
)
from app.assistant_v2.constant import PENDING_RESPONSE_KEY, USER_CHOICE_ID_KEY
from app.core import RequestContext
from app.llm.llm_wrapper import AzureChatOpenAIWrapper
from app.prompt.prompt_service import PromptService


@pytest.fixture(scope="session", autouse=True)
def setup():
    sentry_sdk.init(dsn="")


@pytest.fixture
def prompt_service():
    mock_chat_prompt = MagicMock(
        name="test_prompt",
        chat_messages=[ChatMessageDict(role="system", content="test_prompt")],
        tmpl=ChatPromptTemplate.from_messages([("system", "test_prompt")]),
        llm_model=MagicMock(AzureChatOpenAIWrapper),
    )
    mock_prompt_service = MagicMock(PromptService)
    mock_prompt_service.get_prompt = AsyncMock(return_value=mock_chat_prompt)
    return mock_prompt_service


@pytest.fixture
def mock_token(mocker):
    mock_class = mocker.patch("fastapi.security.HTTPAuthorizationCredentials")
    instance = mock_class.return_value
    instance.credentials = "mock_credentials"
    return instance


@pytest.fixture(scope="function")
def agent_config(prompt_service):
    os.environ["AZURE_OPENAI_ENDPOINT"] = "fake_endpoint"
    os.environ["OPENAI_API_VERSION"] = "fake_version"
    os.environ["AZURE_OPENAI_DEPLOYMENT"] = "fake_deployment"
    os.environ["AZURE_OPENAI_API_KEY"] = "fake_key"  # pragma: allowlist secret
    cache_path = Path(".tmp/assistant_state")
    cache_path.mkdir(parents=True, exist_ok=True)
    os.environ["ASSISTANT_STATE_PATH"] = str(cache_path / "state.db")

    yield {
        CONFIGURABLE_CONTEXT_KEY: {
            THREAD_ID_KEY: str(uuid.uuid1()),
            CONTEXT_KEY: RequestContext("req_id"),
            EBP_ACCESS_TOKEN_KEY: "access_token",
            EBP_COOKIE_KEY: "cookie",
            EBP_EDGE_DOMAIN_KEY: "edge_domain",
            LLM_MODEL_KEY: AzureChatOpenAI(),
            PROMPT_SERVICE_KEY: prompt_service,
            PENDING_RESPONSE_KEY: [],
            USER_CHOICE_ID_KEY: [],
        }
    }
    # remove cached state
    shutil.rmtree(".tmp", ignore_errors=True)


@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m


@pytest.fixture()
def mock_http_request(mocker):
    mocker.patch.object(Request, "headers", {"cookie": "test_cookie"})
    mocker.patch.object(
        Request,
        "cookies",
        {
            "USER_CONTEXT": "test_user_context",
            "ASLBSA": "test_aslbsa",
            "ASLBSACORS": "test_aslbsac",
            "XSRF-TOKEN": "test_token",
        },
    )
    return Request(scope={"type": "http"})


@pytest.fixture()
def _mock_guardrails_config(mocker):
    mocker.patch(
        "nemoguardrails.actions.llm.utils.llm_call",
        return_value=AsyncMock(return_value=None),
    )
    mocker.patch(
        "app.nemo_config.guardrails.load_prompt",
        return_value="""
prompts:\n  - task: self_check_user_query\n    content: Fake prompt for guardrails "{{ user_input }}" prompt\n
        """,
    )

    mocker.patch.object(LLMRails, "register_action", return_value=None)


@pytest.fixture()
def mock_guardrails_pass(mocker, _mock_guardrails_config):
    mock_pass_response = {
        "content": """{
            "message": "No",
            "reason": "The input is valid due to mocking guardrails"
        }"""
    }
    mocker.patch.object(
        LLMRails,
        "generate_async",
        AsyncMock(return_value=mock_pass_response),
    )


@pytest.fixture()
def mock_guardrails_fail(mocker, _mock_guardrails_config):
    mock_fail_response = {
        "content": """{
            "message": "Yes",
            "reason": "The input is invalid due to mocking guardrails"
        }"""
    }
    mocker.patch.object(
        LLMRails,
        "generate_async",
        AsyncMock(return_value=mock_fail_response),
    )
