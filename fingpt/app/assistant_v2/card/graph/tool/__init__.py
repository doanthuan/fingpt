from langgraph.prebuilt import ToolNode

from app.assistant_v2.card.graph.tool.get_card import get_card_tool
from app.assistant_v2.card.graph.tool.get_renewable_card import get_renewable_card_tool
from app.assistant_v2.common.base_graph import NodeName

tool_list = [get_card_tool, get_renewable_card_tool]

tool_node_executable = ToolNode(tool_list)
tool_node = NodeName("tool_node")

__all__ = [
    "tool_list",
    "tool_node",
    "tool_node_executable",
    "get_card_tool",
    "get_renewable_card_tool",
]
