from typing import Any, Dict


def get_assert(output: Dict[str, Any], context: Dict[str, Any]):
    tool_calls = output["tool_calls"]

    is_pass = True
    reason = ""
    if not tool_calls:
        is_pass = False
        reason = "No tool call found."

    tool_names = [tool_call["name"] for tool_call in tool_calls]
    if "NoticeTransferAmountTool" not in tool_names:
        is_pass = False
        reason = "Tool call name should be NoticeTransferAmountTool."
    else:
        tool_idx = tool_names.index("NoticeTransferAmountTool")
        tool = tool_calls[tool_idx]
        if "args" not in tool or "amount" not in tool["args"]:
            is_pass = False
            reason = "Amount not found in tool call."

    return {
        "pass": is_pass,
        "score": 1.0 if is_pass else 0.0,
        "reason": reason,
    }
