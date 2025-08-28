from typing import Any, Dict


def get_assert(output: Dict[str, Any], context: Dict[str, Any]):
    tool_calls = output["tool_calls"]

    is_pass = True
    reason = ""
    if not tool_calls:
        is_pass = False
        reason = "No tool call found."

    tool_names = [tool_call["name"] for tool_call in tool_calls]
    if "NoticeDepositAmountTool" not in tool_names:
        is_pass = False
        reason = "Tool call name should be NoticeDepositAmountTool."
    tool_index = tool_names.index("NoticeDepositAmountTool")
    tool = tool_calls[tool_index]
    if "args" not in tool:
        is_pass = False
        reason = "Output should contain 'args' key."
    elif "deposit_amount" not in tool["args"] or tool["args"]["deposit_amount"] <= 0:
        is_pass = False
        reason = "Deposit amount should be greater than 0."

    return {
        "pass": is_pass,
        "score": 1.0 if is_pass else 0.0,
        "reason": reason,
    }
