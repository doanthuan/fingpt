from typing import Any, Dict


def get_assert(output: Dict[str, Any], context: Dict[str, Any]):
    tool_calls = output.get("tool_calls", [])

    is_pass = True
    reason = ""

    if not tool_calls:
        is_pass = False
        reason = "No tool calls found."
    if len(tool_calls) > 1:
        is_pass = False
        reason = "More than one tool call found."

    if tool_calls[0]["name"] != "ToReportGenerator":
        is_pass = False
        reason = "Tool call is not ToReportGenerator."

    return {
        "pass": is_pass,
        "score": 1 if is_pass else 0,
        "reason": reason,
    }
