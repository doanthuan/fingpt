from langgraph.prebuilt import ToolNode

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.transfer.graph.tool.get_accounts import get_account_tool
from app.assistant_v2.transfer.graph.tool.get_contacts import get_contact_tool
from app.assistant_v2.transfer.graph.tool.notice_transfer_amount import (
    notice_transfer_amount_tool,
)

tool_list = [get_contact_tool, get_account_tool, notice_transfer_amount_tool]
tool_names = [tool.name for tool in tool_list]
tool_node_executable = ToolNode(tool_list)
tool_node = NodeName("tool_node")

__all__ = [
    "tool_list",
    "tool_names",
    "tool_node",
    "tool_node_executable",
    "get_account_tool",
    "get_contact_tool",
    "notice_transfer_amount_tool",
]
