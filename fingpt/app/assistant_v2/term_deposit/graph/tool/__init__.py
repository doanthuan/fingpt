from langgraph.prebuilt import ToolNode

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.term_deposit.graph.tool.get_accounts import get_account_tool
from app.assistant_v2.term_deposit.graph.tool.get_term_deposit_accounts import (
    get_term_deposit_account_tool,
)
from app.assistant_v2.term_deposit.graph.tool.get_term_deposit_products import (
    get_term_deposit_product_tool,
)
from app.assistant_v2.term_deposit.graph.tool.notice_deposit_amount import (
    notice_desposit_amount_tool,
)
from app.assistant_v2.term_deposit.graph.tool.notice_term_number import (
    notice_term_number_tool,
)
from app.assistant_v2.term_deposit.graph.tool.notice_term_unit import (
    notice_term_unit_tool,
)

tool_list = [
    get_account_tool,
    get_term_deposit_account_tool,
    get_term_deposit_product_tool,
    notice_desposit_amount_tool,
    notice_term_number_tool,
    notice_term_unit_tool,
]
tool_names = [tool.name for tool in tool_list]
tool_node_executable = ToolNode(tool_list)
tool_node = NodeName("tool_node")

__all__ = [
    "tool_list",
    "tool_names",
    "tool_node",
    "tool_node_executable",
    "get_account_tool",
    "get_term_deposit_account_tool",
    "get_term_deposit_product_tool",
    "notice_desposit_amount_tool",
    "notice_term_number_tool",
    "notice_term_unit_tool",
]
