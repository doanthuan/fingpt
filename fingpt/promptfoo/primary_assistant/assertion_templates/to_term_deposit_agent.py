from typing import Any, Dict


def get_assert(output: Dict[str, Any], context: Dict[str, Any]):
    tool_calls = output["tool_calls"]

    is_pass = True
    reason = ""
    if not tool_calls:
        is_pass = False
        reason = "No tool call found."
    elif len(tool_calls) != 1:
        is_pass = False
        reason = "Only one tool call is allowed."
    elif tool_calls[0]["name"] != "ToTermDepositAgent":
        is_pass = False
        reason = "Tool call name should be ToTermDepositAgent."
    elif tool_calls[0]["type"] != "tool_call":
        is_pass = False
        reason = "Tool call type should be tool_call."

    return {
        "pass": is_pass,
        "score": 1.0 if is_pass else 0.0,
        "reason": reason,
    }
