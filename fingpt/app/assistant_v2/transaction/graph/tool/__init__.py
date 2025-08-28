from langgraph.prebuilt import ToolNode

from app.assistant_v2.common.base_graph import NodeName

from .filter_transaction import filter_transaction_tool

tool_list = [filter_transaction_tool]
tool_node_executable = ToolNode(tool_list)
tool_node = NodeName("tool_node")


__all__ = [
    "tool_list",
    "tool_node",
    "tool_node_executable",
    "filter_transaction_tool",
]
