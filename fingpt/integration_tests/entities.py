from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class APIConfig(BaseModel):
    name: str
    login_required: bool
    api_url: str
    method: str
    testcases_path: str
    batch_size: int = 1
    timeout: int = 60


class LoginAPIInfo(BaseModel):
    api_url: str
    input_username: str
    input_password_env: str
    user_type: str = "retail"
    access_token_field: str
    cookie_field: str


class IntegrationTestConfig(BaseModel):
    configs: List[APIConfig]
    login_api: LoginAPIInfo


class AssertMethods(str, Enum):
    EQUALS = "equals"
    CONTAINS_KEYS = "contains_keys"
    KEY_AND_TYPE = "key_and_type"
    LLM_FLEXIBLE = "llm_flexible"


class AdditionalAssertInput(BaseModel):
    input_material: Optional[str] = None
    max_reply: Optional[int] = 3
    reply_count: Optional[int] = 3  # set to equal to max_reply to avoid infinite loop
    final_assert_method: AssertMethods = AssertMethods.EQUALS


class TestOutput(BaseModel):
    status: int
    response: dict


class TestStep(BaseModel):
    name: str
    assert_method: AssertMethods
    additional_assert_input: Optional[AdditionalAssertInput] = None
    input: dict
    output: TestOutput


class TestCase(BaseModel):
    name: str
    steps: list[TestStep]


class TestCases(BaseModel):
    testcases: List[TestCase]
