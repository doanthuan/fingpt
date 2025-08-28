from typing import Any, Dict, TypedDict, Union


def get_assert(
    output: Dict[str, Any], context: TypedDict
) -> Union[bool, float, Dict[str, Any]]:
    tool_calls = output["tool_calls"]

    is_pass = True
    reason = ""
    if not tool_calls:
        is_pass = False
        reason = "No tool call found."
    elif len(tool_calls) != 1:
        is_pass = False
        reason = "Only one tool call is allowed."
    elif tool_calls[0]["name"] != "GetRenewableCardTool":
        is_pass = False
        reason = "Tool call name should be GetRenewableCardTool."
    elif tool_calls[0]["type"] != "tool_call":
        is_pass = False
        reason = "Tool call type should be tool_call."
    elif "args" not in tool_calls[0] or "expired_days" not in tool_calls[0]["args"]:
        is_pass = False
        reason = "Tool call should have expired_days in args."

    return {
        "pass": is_pass,
        "score": 1.0 if is_pass else 0.0,
        "reason": reason,
    }
