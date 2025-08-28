from typing import Any

from langchain_core.messages import AnyMessage, ToolCall, ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode

from app.assistant_v2.primary.state import AssistantState


def handle_tool_error(state: AssistantState) -> dict[str, Any]:
    error: Any = state.get("error")
    messages: list[AnyMessage] = state.get("messages")
    tool_calls: list[ToolCall] = messages[-1].tool_calls  # type: ignore
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls  # type: ignore
        ]
    }


def create_tool_node_with_fallback(
    tools: list[ToolNode],
) -> dict[str, Any]:
    return ToolNode(tools).with_fallbacks(  # type: ignore
        [RunnableLambda(handle_tool_error)],
        exception_key="error",
    )
