from typing import Any, Dict, TypedDict, Union

from app.entity.api import SupportedTicker


def get_assert(output: Dict, context: TypedDict) -> Union[bool, float, Dict[str, Any]]:
    tool_calls = output["tool_calls"]

    is_pass = True
    reason = ""
    if not tool_calls:
        is_pass = False
        reason = "No tool call found."
    elif len(tool_calls) != 1:
        is_pass = False
        reason = "Only one tool call is allowed."
    elif tool_calls[0]["name"] != "ToReportGenerator":
        is_pass = False
        reason = "Tool call name should be ToReportGenerator."
    elif tool_calls[0]["type"] != "tool_call":
        is_pass = False
        reason = "Tool call type should be tool_call."
    elif "args" not in tool_calls[0] or "ticker_symbol" not in tool_calls[0]["args"]:
        is_pass = False
        reason = "Tool call should have ticker_symbol in args."
    if is_pass:
        ticker_symbol = tool_calls[0]["args"].get("ticker_symbol", "")
        supported_ticker = SupportedTicker.has_value(ticker_symbol)
        if not supported_ticker:
            is_pass = False
            reason = "Unsupported ticker symbol"

    return {
        "pass": is_pass,
        "score": 1.0 if is_pass else 0.0,
        "reason": reason,
    }
