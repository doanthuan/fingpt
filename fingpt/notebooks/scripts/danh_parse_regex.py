# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.7
#   kernelspec:
#     display_name: fingpt-VvNJuklE-py3.11
#     language: python
#     name: python3
# ---

# %%
import sys

sys.path.append("../..")
from integration_tests.entities import TestOutput
import re


# %%
def _extract_prev_output_data(key: str, response: list[TestOutput]) -> dict:
    parts = key.split(".")
    if len(parts) == 1:
        assert "steps" in parts[0]
        step_index = eval(parts[0].replace("steps", ""))[0]
        return response[step_index].model_dump()
    assert "steps" in parts[0]
    step_index = eval(parts[0].replace("steps", ""))[0]
    current = response[step_index].model_dump()
    parts = parts[1:]
    for p in parts:
        if "[" in p and "]" in p:
            print(p)
            key_name, idx = re.match(r"(.+?)\[(\d+)]", p).groups()
            print(key_name, idx)
            current = current.get(key_name)[int(idx)]
        else:
            current = current.get(p)
    return current


# %%
_extract_prev_output_data(
    "steps[0].response.a[0].id",
    [TestOutput(status=200, response={"a": [{"id": 1}]})],
)

# %%
pattern = r"\$\{?(.*)\}?"
text1 = "${steps[0].abc.xyz}"
text2 = "this is a normal text"
text3 = "$abc"
match1 = re.search(pattern, text1)
match2 = re.search(pattern, text2)
match3 = re.search(pattern, text3)
print(re.search(pattern, text1))
print(re.search(pattern, text2))
print(re.search(pattern, text3))

# %%
print(match1.groups())
print(match3.groups())

# %%
match1.groups()[0][:-1]


# %%
def _extract_prev_output_data(key: str, responses: list[TestOutput]) -> dict:
    parts = key.split(".")
    if len(parts) == 1:
        assert "steps" in parts[0]
        step_index = eval(parts[0].replace("steps", ""))[0]
        return responses[step_index].model_dump()
    assert "steps" in parts[0]
    step_index = eval(parts[0].replace("steps", ""))[0]
    current = responses[step_index].model_dump()
    parts = parts[1:]
    for p in parts:
        if "[" in p and "]" in p:
            key_name, idx = re.match(r"(.+?)\[(\d+)]", p).groups()
            current = current.get(key_name)[int(idx)]
        else:
            current = current.get(p)
    return current


def _compile_input(test_input: dict, responses: list[TestOutput]) -> dict:
    compiled_input = {}
    pattern = r"\$\{?(.*)\}?"  # regex pattern to extract value in ${} or $
    for key, value in test_input.items():
        if isinstance(value, str):
            matches = re.search(pattern, value)
            if matches:
                response_key = matches.groups()[0][:-1]
                prev_output_data = _extract_prev_output_data(response_key, responses)
                compiled_input[key] = prev_output_data
            else:
                compiled_input[key] = value
        elif isinstance(value, dict):
            compiled_input[key] = _compile_input(value, responses)
        else:
            compiled_input[key] = value

    return compiled_input


# %%
test_input = {
    "a": "normal",
    "b": "${steps[0].status}",
    "c": {"x": "${steps[1].response.a[0].idx}"},
}
responses = [
    TestOutput(status=200, response={"a": 100}),
    TestOutput(status=200, response={"a": [{"idx": 10}, {"idx": 20}]}),
]
_compile_input(test_input, responses)

# %%
