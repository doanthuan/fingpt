import json
from typing import Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langfuse.utils.langfuse_singleton import LangfuseSingleton

from app.core.config import settings
from app.entity import ChatRespAction
from app.llm.llm_wrapper import AzureChatOpenAIWrapper
from integration_tests.entities import AdditionalAssertInput, AssertMethods


def _get_llm_model():
    return AzureChatOpenAIWrapper(
        azure_deployment=settings.azure_openai_deployment,
        temperature=settings.llm_temperature,
    )


def _get_instruction_prompt_template():
    langfuse = LangfuseSingleton().get()
    instruction = langfuse.get_prompt(
        name="retail.integration-test.azure-openai.reply-instruction",
        label="latest",
        type="chat",
    )
    return ChatPromptTemplate.from_messages(instruction.get_langchain_prompt())


# call assert method by function's name
def call_assert_method(
    method_name: AssertMethods,
    actual: Any,
    expected: dict,
    additional_assert_input: AdditionalAssertInput = None,
):
    assert_method = globals().get(method_name.value)
    assert assert_method, f"Method {method_name} not found"
    return assert_method(actual, expected, additional_assert_input)


def equals(actual: dict | str, expected: dict, _: AdditionalAssertInput):
    if isinstance(actual, str):
        actual = json.loads(actual)
    # check if actual contains all keys in expected and their values are equal
    assert (
        actual.keys() == expected.keys()
    ), f"Keys mismatch, expected {expected.keys()}, got {actual.keys()}"
    for key, value in expected.items():
        assert actual[key] == value, f"Expected {value} for {key}, got {actual}"
    return True


def contains_keys(
    actual: dict | str, expected: dict, _: Optional[AdditionalAssertInput] = None
):
    if isinstance(actual, str):
        actual = json.loads(actual)
    # check if actual contains all keys in expected and their values are equal
    for key, value in expected.items():
        assert key in actual, f"Key {key} not found in actual"
        if isinstance(value, dict):
            assert isinstance(
                actual[key], dict
            ), f"Expected dict for {key}, got {type(actual[key])}"
            contains_keys(actual[key], value, None)
        else:
            if isinstance(value, str) and "|" in value:
                values = [v.strip() for v in value.split("|")]
                assert (
                    actual[key] in values
                ), f"Expected {values} for {key}, got {actual}"
            else:
                assert actual[key] == value, f"Expected {value} for {key}, got {actual}"
    return True


def _type_by_name(name: str):
    type_mapping = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "tuple": tuple,
    }
    assert name in type_mapping, f"Type {name} not found"
    return type_mapping[name]


def key_and_type(actual: dict | str, expected: dict, _: AdditionalAssertInput):
    if isinstance(actual, str):
        actual = json.loads(actual)
    for key, expected_type in expected.items():
        assert key in actual, f"Key {key} not found in actual"
        assert isinstance(
            actual[key], _type_by_name(expected_type)
        ), f"Type mismatch for key {key}, expected {expected_type}, got {type(actual[key])}"
    return True


def llm_flexible(
    actual: dict | str, expected: dict, additional_input: AdditionalAssertInput
) -> str | bool:
    if isinstance(actual, str):
        actual = json.loads(actual)
    if additional_input.reply_count > additional_input.max_reply:
        raise AssertionError("Exceeded max reply count")
    assert_method = globals().get(additional_input.final_assert_method.value)
    try:
        assert_method(actual, expected)
        return True
    except AssertionError as _:  # noqa: F841
        pass

    # using AI to handle flex response
    assert (
        actual["action"] == ChatRespAction.SHOW_REPLY
    ), "llm_flex_assert expect action to be SHOW_REPLY"

    llm = _get_llm_model()
    prompt_tmpl = _get_instruction_prompt_template()
    chain = prompt_tmpl | llm
    new_query = chain.invoke(
        input={
            "input_material": additional_input.input_material,
            "api_response": actual["response"],
        }
    )
    return new_query.content
