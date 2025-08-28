from typing import Any, Literal

from app.assistant_v2.primary.tool.to_term_deposit_agent import ToTermDepositAgent
from app.assistant_v2.util.complete_or_escalate import CompleteOrEscalateTool

from .tool.to_card_agent import ToCardAgent
from .tool.to_card_flow import ToCardFlow
from .tool.to_term_deposit_flow import ToTermDepositFlow
from .tool.to_ticker_agent import ToTickerAgent
from .tool.to_transaction_agent import ToTransactionAgent
from .tool.to_transfer_agent import ToTransferAgent

DialogController = Literal[
    "PRIMARY_ASSISTANT",
    "TICKER_AGENT",
    "TRANSACTION_AGENT",
    "TRANSFER_AGENT",
    "TERM_DEPOSIT_CONTROLLER",
    "CARD_CONTROLLER",
]

ENTER_TICKER_AGENT_NODE = "enter_ticker_agent_node"
TICKER_AGENT_NODE = "TICKER_AGENT"
TICKER_AGENT_NAME = "Public Ticker Analyst"
TICKER_AGENT_TOOLS_NODE = "ticker_agent_tools_node"
TICKER_AGENT_ROUTE = Literal[
    "prepare_response_node",
    "return_control_node",
    "ticker_agent_tools_node",
]

RETURN_CONTROL_NODE = "return_control_node"
DELETE_OLD_MESSAGE_NODE = "delete_old_message_node"

PRIMARY_ASSISTANT_NODE = "PRIMARY_ASSISTANT"
PRIMARY_ASSISTANT_TOOLS_NODE = "primary_assistant_tools_node"
PRIMARY_ASSISTANT_TOOLS: list[Any] = [
    ToTickerAgent,
    ToTransactionAgent,
    ToTransferAgent,
    ToTermDepositAgent,
    ToCardAgent,
]
PRIMARY_ASSISTANT_ROUTE = Literal[
    "prepare_response_node",
    "enter_ticker_agent_node",
    "enter_transaction_agent_node",
    "enter_transfer_agent_node",
    "primary_assistant_tools_node",
    "enter_term_deposit_controller_node",
    "enter_card_controller_node",
]

SUBGRAPH_ENTER_CONTENT = (
    "Acknowledged! Now you are in {agent}."
    " Continue to service user's request by calling a tool in system instruction."
)

# CONTROLLER_ENTER_CONTENT = "Control successfully transferred to {controller} ! Continue to service user's request."
CONTROLLER_ENTER_CONTENT = SUBGRAPH_ENTER_CONTENT

CONTROLLER_EXIT_CONTENT = (
    "Resuming dialog with the host primary assistant. "
    "Continue to service user's request."
)
CONTROLLER_EXIT_WITH_SUMMARY = (
    "{agent} exited, reason: {reason}, find the summary above. "
    "Resuming dialog with the host primary assistant. "
    "Continue to service user's request."
)
ENTER_TRANSACTION_AGENT_NODE = "enter_transaction_agent_node"
ENTER_TRANSACTION_REPORT_GENERATOR_SUBGRAPH_NODE = (
    "enter_transaction_report_generator_subgraph_node"
)
ENTER_TRANSACTION_REPORT_GENERATOR_SUBGRAPH_NAME = (
    "Transaction Report Generator Subgraph"
)
TRANSACTION_AGENT_NODE = "TRANSACTION_AGENT"
TRANSACTION_AGENT_NAME = "Transaction Analyst"
TRANSACTION_AGENT_TOOLS_NODE = "transaction_agent_tools_node"
TRANSACTION_REPORT_GENERATOR_NODE = "transaction_report_generator_node"
TRANSACTION_AGENT_ROUTE = Literal[
    "prepare_response_node",
    "return_control_node",
    "enter_transaction_report_generator_subgraph_node",
    "transaction_agent_tools_node",
]

ENTER_TRANSFER_AGENT_NODE = "enter_transfer_agent_node"
TRANSFER_AGENT_NAME = "Money Transfer Assistant"
TRANSFER_AGENT_NODE = "TRANSFER_AGENT"
TRANSFER_AGENT_TOOLS_NODE = "transfer_agent_tools_node"
ENTER_MONEY_TRANSFER_SUBGRAPH_NODE = "enter_money_transfer_subgraph_node"
ENTER_MONEY_TRANSFER_SUBGRAPH_NAME = "Money Transfer Subgraph"
MONEY_TRANSFER_WORKFLOW_NODE = "money_transfer_workflow_node"
TRANSFER_AGENT_ROUTE = Literal[
    "prepare_response_node",
    "return_control_node",
    "enter_money_transfer_subgraph_node",
    "transfer_agent_tools_node",
]

PREPARE_RESPONSE_NODE = "prepare_response_node"

GUARDRAIL_ERROR_CONTENT = (
    "As a banking assistant, I could not answer your query. "
    "Please try again with a different input."
)

TRANSACTION_START_ROUTE = Literal[
    "filter_transaction",
    "select_beneficiary_node",
]

TRANSFER_START_ROUTE = Literal[
    "call_model",
    "select_contact",
    "select_account",
]

AGAINST_POLICY_CONTENT = (
    "Sorry, your input is against our policies. I can't service your request."
)

ENTER_TERM_DEPOSIT_CONTROLLER_NODE = "enter_term_deposit_controller_node"
TERM_DEPOSIT_CONTROLLER_NODE = "TERM_DEPOSIT_CONTROLLER"
TERM_DEPOSIT_CONTROLLER_NAME = "Term Deposit Controller"
ENTER_TERM_DEPOSIT_SUBGRAPH_NODE = "enter_term_deposit_subgraph_node"
ENTER_TERM_DEPOSIT_SUBGRAPH_NAME = "Term Deposit Subgraph"
TERM_DEPOSIT_WORKFLOW_NODE = "term_deposit_workflow_node"
TERM_DEPOSIT_CONTROLLER_TOOLS_NODE = "term_deposit_controller_tools_node"

TERM_DEPOSIT_CONTROLLER_TOOLS: list[Any] = [
    ToTermDepositFlow,
    CompleteOrEscalateTool,
]

ENTER_CARD_CONTROLLER_NODE = "enter_card_controller_node"
CARD_CONTROLLER_NODE = "CARD_CONTROLLER"
CARD_CONTROLLER_NAME = "Card Controller"
ENTER_CARD_SUBGRAPH_NODE = "enter_card_subgraph_node"
ENTER_CARD_SUBGRAPH_NAME = "Card Subgraph"
CARD_WORKFLOW_NODE = "card_workflow_node"
CARD_CONTROLLER_TOOLS_NODE = "card_controller_tools_node"

CARD_CONTROLLER_TOOLS: list[Any] = [
    ToCardFlow,
    CompleteOrEscalateTool,
]
