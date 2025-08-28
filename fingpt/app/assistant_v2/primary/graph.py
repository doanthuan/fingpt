from typing import get_args, no_type_check

from langchain_openai import AzureChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition

from app.assistant_v2.card.graph.card_graph import CardGraph
from app.assistant_v2.primary.node import (
    controller_enter_node,
    controller_exit_node,
    delete_message,
    prepare_response_node,
    subgraph_enter_node,
    wrap_agent_node,
)
from app.assistant_v2.primary.tool.to_card_agent import ToCardAgent
from app.assistant_v2.primary.tool.to_term_deposit_agent import ToTermDepositAgent
from app.assistant_v2.primary.tool.to_transfer_agent import ToTransferAgent
from app.assistant_v2.term_deposit.graph.term_deposit_graph import TermDepositGraph
from app.assistant_v2.ticker.constant import TICKER_AGENT_TOOLS
from app.assistant_v2.ticker.symbol_identifier_agent import SymbolIdentifierAgent
from app.assistant_v2.transaction.constant import TRANSACTION_AGENT_TOOLS
from app.assistant_v2.transaction.graph.transaction_agent_graph import TransactionGraph
from app.assistant_v2.transaction.tool.to_report_generator import ToReportGenerator
from app.assistant_v2.transfer.constant import TRANSFER_AGENT_TOOLS
from app.assistant_v2.transfer.graph.transfer_graph import TransferGraph
from app.assistant_v2.transfer.money_transfer_agent import MoneyTransferAgent
from app.assistant_v2.transfer.tool.to_transfer_money_flow import ToMoneyTransferFlow
from app.assistant_v2.util.complete_or_escalate import CompleteOrEscalateTool
from app.assistant_v2.util.create_tool import create_tool_node_with_fallback
from app.prompt.prompt_service import PromptService

from .assistant import Assistant
from .card_controller import CardController
from .constant import (
    CARD_CONTROLLER_NODE,
    CARD_CONTROLLER_TOOLS,
    CARD_CONTROLLER_TOOLS_NODE,
    CARD_WORKFLOW_NODE,
    DELETE_OLD_MESSAGE_NODE,
    ENTER_CARD_CONTROLLER_NODE,
    ENTER_CARD_SUBGRAPH_NAME,
    ENTER_CARD_SUBGRAPH_NODE,
    ENTER_MONEY_TRANSFER_SUBGRAPH_NAME,
    ENTER_MONEY_TRANSFER_SUBGRAPH_NODE,
    ENTER_TERM_DEPOSIT_CONTROLLER_NODE,
    ENTER_TERM_DEPOSIT_SUBGRAPH_NAME,
    ENTER_TERM_DEPOSIT_SUBGRAPH_NODE,
    ENTER_TICKER_AGENT_NODE,
    ENTER_TRANSACTION_AGENT_NODE,
    ENTER_TRANSACTION_REPORT_GENERATOR_SUBGRAPH_NAME,
    ENTER_TRANSACTION_REPORT_GENERATOR_SUBGRAPH_NODE,
    ENTER_TRANSFER_AGENT_NODE,
    MONEY_TRANSFER_WORKFLOW_NODE,
    PREPARE_RESPONSE_NODE,
    PRIMARY_ASSISTANT_NODE,
    PRIMARY_ASSISTANT_ROUTE,
    PRIMARY_ASSISTANT_TOOLS,
    PRIMARY_ASSISTANT_TOOLS_NODE,
    RETURN_CONTROL_NODE,
    TERM_DEPOSIT_CONTROLLER_NODE,
    TERM_DEPOSIT_CONTROLLER_TOOLS,
    TERM_DEPOSIT_CONTROLLER_TOOLS_NODE,
    TERM_DEPOSIT_WORKFLOW_NODE,
    TICKER_AGENT_NODE,
    TICKER_AGENT_ROUTE,
    TICKER_AGENT_TOOLS_NODE,
    TRANSACTION_AGENT_NODE,
    TRANSACTION_AGENT_ROUTE,
    TRANSACTION_AGENT_TOOLS_NODE,
    TRANSACTION_REPORT_GENERATOR_NODE,
    TRANSFER_AGENT_NODE,
    TRANSFER_AGENT_ROUTE,
    TRANSFER_AGENT_TOOLS_NODE,
    DialogController,
)
from .state import AssistantConfig, AssistantState, AssistantStateFields
from .term_deposit_controller import TermDepositController
from .tool.to_card_flow import ToCardFlow
from .tool.to_term_deposit_flow import ToTermDepositFlow
from .tool.to_ticker_agent import ToTickerAgent
from .tool.to_transaction_agent import ToTransactionAgent
from .transaction_report_agent import TransactionReportAgent


class AssistantGraph:
    def __init__(
        self,
        prompt_srv: PromptService,
        llm: AzureChatOpenAI,
    ):
        self.prompt_srv = prompt_srv
        self.llm = llm

    @staticmethod
    @no_type_check
    def route_ticker_agent_to_tools(
        state: AssistantState,
    ) -> TICKER_AGENT_ROUTE:
        messages = state[AssistantStateFields.MESSAGES]
        route = tools_condition(messages)
        if route == END:
            return PREPARE_RESPONSE_NODE

        tool_calls = messages[-1].tool_calls
        if tool_calls:
            did_exit = any(
                tc["name"] == CompleteOrEscalateTool.__name__ for tc in tool_calls
            )
            if did_exit:
                return RETURN_CONTROL_NODE

        return TICKER_AGENT_TOOLS_NODE

    @staticmethod
    @no_type_check
    def route_transaction_agent_to_tools(
        state: AssistantState,
    ) -> TRANSACTION_AGENT_ROUTE:
        messages = state[AssistantStateFields.MESSAGES]
        route = tools_condition(messages)
        if route == END:
            return PREPARE_RESPONSE_NODE

        tool_calls = messages[-1].tool_calls
        if tool_calls:
            did_exit = any(
                tc["name"] == CompleteOrEscalateTool.__name__ for tc in tool_calls
            )
            if did_exit:
                return RETURN_CONTROL_NODE

            if tool_calls[0]["name"] == ToReportGenerator.__name__:
                return ENTER_TRANSACTION_REPORT_GENERATOR_SUBGRAPH_NODE

        return TRANSACTION_AGENT_TOOLS_NODE

    @staticmethod
    @no_type_check
    def route_transfer_agent_to_tools(
        state: AssistantState,
    ) -> TRANSFER_AGENT_ROUTE:
        messages = state[AssistantStateFields.MESSAGES]
        route = tools_condition(messages)
        if route == END:
            return PREPARE_RESPONSE_NODE

        tool_calls = messages[-1].tool_calls
        if tool_calls:
            did_exit = any(
                tc["name"] == CompleteOrEscalateTool.__name__ for tc in tool_calls
            )
            if did_exit:
                return RETURN_CONTROL_NODE

            if tool_calls[0]["name"] == ToMoneyTransferFlow.__name__:
                return ENTER_MONEY_TRANSFER_SUBGRAPH_NODE

        return TRANSFER_AGENT_TOOLS_NODE

    @staticmethod
    @no_type_check
    def route_term_deposit_controller_to_tools(
        state: AssistantState,
    ) -> str:
        messages = state[AssistantStateFields.MESSAGES]
        route = tools_condition(messages)
        if route == END:
            return PREPARE_RESPONSE_NODE

        tool_calls = messages[-1].tool_calls
        if tool_calls:
            did_exit = any(
                tc["name"] == CompleteOrEscalateTool.__name__ for tc in tool_calls
            )
            if did_exit:
                return RETURN_CONTROL_NODE

            if tool_calls[0]["name"] == ToTermDepositFlow.__name__:
                return ENTER_TERM_DEPOSIT_SUBGRAPH_NODE

        return TERM_DEPOSIT_CONTROLLER_TOOLS_NODE

    @staticmethod
    @no_type_check
    def route_card_controller_to_tools(
        state: AssistantState,
    ) -> str:
        messages = state[AssistantStateFields.MESSAGES]
        route = tools_condition(messages)
        if route == END:
            return PREPARE_RESPONSE_NODE

        tool_calls = messages[-1].tool_calls
        if tool_calls:
            did_exit = any(
                tc["name"] == CompleteOrEscalateTool.__name__ for tc in tool_calls
            )
            if did_exit:
                return RETURN_CONTROL_NODE

            if tool_calls[0]["name"] == ToCardFlow.__name__:
                return ENTER_CARD_SUBGRAPH_NODE

        return CARD_CONTROLLER_TOOLS_NODE

    @staticmethod
    @no_type_check
    def route_primary_assistant_to_tools(
        state: AssistantState,
    ) -> PRIMARY_ASSISTANT_ROUTE:
        messages = state[AssistantStateFields.MESSAGES]
        route = tools_condition(messages)
        if route == END:
            return PREPARE_RESPONSE_NODE

        tool_calls = messages[-1].tool_calls
        if tool_calls:
            if tool_calls[0]["name"] == ToTickerAgent.__name__:
                return ENTER_TICKER_AGENT_NODE

            elif tool_calls[0]["name"] == ToTransactionAgent.__name__:
                return ENTER_TRANSACTION_AGENT_NODE

            elif tool_calls[0]["name"] == ToTransferAgent.__name__:
                return ENTER_TRANSFER_AGENT_NODE

            elif tool_calls[0]["name"] == ToTermDepositAgent.__name__:
                return ENTER_TERM_DEPOSIT_CONTROLLER_NODE

            elif tool_calls[0]["name"] == ToCardAgent.__name__:
                return ENTER_CARD_CONTROLLER_NODE

        return PRIMARY_ASSISTANT_TOOLS_NODE

    @staticmethod
    def direct_workflow_router(
        state: AssistantState,
    ) -> DialogController:
        controller_stack = state.get(AssistantStateFields.CONTROLLER_STACK, None)
        if not controller_stack:
            return PRIMARY_ASSISTANT_NODE
        return controller_stack[-1]

    async def get_graph(self) -> StateGraph:
        workflow = StateGraph(
            state_schema=AssistantState,
            config_schema=AssistantConfig,
        )

        workflow.add_node(
            PREPARE_RESPONSE_NODE,
            prepare_response_node,
        )

        workflow.add_edge(
            PREPARE_RESPONSE_NODE,
            END,
        )

        """SETTING UP THE TICKER AGENT"""

        workflow.add_node(
            ENTER_TICKER_AGENT_NODE,
            controller_enter_node(
                assistant_name=ToTickerAgent.__name__,
                controller=TICKER_AGENT_NODE,
            ),
        )

        workflow.add_node(
            TICKER_AGENT_NODE,
            SymbolIdentifierAgent(
                prompt_srv=self.prompt_srv,
                llm=self.llm,
            ),
        )

        workflow.add_edge(
            ENTER_TICKER_AGENT_NODE,
            TICKER_AGENT_NODE,
        )
        workflow.add_node(
            TICKER_AGENT_TOOLS_NODE, create_tool_node_with_fallback(TICKER_AGENT_TOOLS)
        )

        workflow.add_conditional_edges(
            TICKER_AGENT_NODE,
            self.route_ticker_agent_to_tools,
            list(get_args(TICKER_AGENT_ROUTE)),
        )
        workflow.add_edge(
            TICKER_AGENT_TOOLS_NODE,
            TICKER_AGENT_NODE,
        )

        """SETTING UP THE TRANSACTION AGENT"""

        workflow.add_node(
            ENTER_TRANSACTION_AGENT_NODE,
            controller_enter_node(
                assistant_name=ToTransactionAgent.__name__,
                controller=TRANSACTION_AGENT_NODE,
            ),
        )

        workflow.add_node(
            TRANSACTION_AGENT_NODE,
            TransactionReportAgent(
                prompt_srv=self.prompt_srv,
                llm=self.llm,
            ),
        )

        workflow.add_edge(
            ENTER_TRANSACTION_AGENT_NODE,
            TRANSACTION_AGENT_NODE,
        )

        workflow.add_node(
            TRANSACTION_AGENT_TOOLS_NODE,
            create_tool_node_with_fallback(TRANSACTION_AGENT_TOOLS),
        )

        workflow.add_node(
            ENTER_TRANSACTION_REPORT_GENERATOR_SUBGRAPH_NODE,
            subgraph_enter_node(ENTER_TRANSACTION_REPORT_GENERATOR_SUBGRAPH_NAME),
        )

        workflow.add_node(
            TRANSACTION_REPORT_GENERATOR_NODE,
            await wrap_agent_node(
                (await TransactionGraph().get_workflow()).compile(),
                AssistantStateFields.TRANSACTION_REPORT_AGENT_STATE,
            ),
        )

        workflow.add_edge(
            ENTER_TRANSACTION_REPORT_GENERATOR_SUBGRAPH_NODE,
            TRANSACTION_REPORT_GENERATOR_NODE,
        )

        workflow.add_edge(
            TRANSACTION_REPORT_GENERATOR_NODE,
            PREPARE_RESPONSE_NODE,
        )

        workflow.add_conditional_edges(
            TRANSACTION_AGENT_NODE,
            self.route_transaction_agent_to_tools,
            list(get_args(TRANSACTION_AGENT_ROUTE)),
        )
        workflow.add_edge(
            TRANSACTION_AGENT_TOOLS_NODE,
            TRANSACTION_AGENT_NODE,
        )

        """SETTING UP THE TRANSFER AGENT"""

        workflow.add_node(
            ENTER_TRANSFER_AGENT_NODE,
            controller_enter_node(
                assistant_name=ToTransferAgent.__name__,
                controller=TRANSFER_AGENT_NODE,
            ),
        )

        workflow.add_node(
            TRANSFER_AGENT_NODE,
            MoneyTransferAgent(
                prompt_srv=self.prompt_srv,
                llm=self.llm,
            ),
        )

        workflow.add_edge(
            ENTER_TRANSFER_AGENT_NODE,
            TRANSFER_AGENT_NODE,
        )

        workflow.add_node(
            TRANSFER_AGENT_TOOLS_NODE,
            create_tool_node_with_fallback(TRANSFER_AGENT_TOOLS),
        )

        workflow.add_node(
            ENTER_MONEY_TRANSFER_SUBGRAPH_NODE,
            subgraph_enter_node(ENTER_MONEY_TRANSFER_SUBGRAPH_NAME),
        )

        workflow.add_node(
            MONEY_TRANSFER_WORKFLOW_NODE,
            await wrap_agent_node(
                (await TransferGraph().get_workflow()).compile(),
                AssistantStateFields.TRANSFER_AGENT_STATE,
            ),
        )

        workflow.add_edge(
            ENTER_MONEY_TRANSFER_SUBGRAPH_NODE,
            MONEY_TRANSFER_WORKFLOW_NODE,
        )

        workflow.add_edge(
            MONEY_TRANSFER_WORKFLOW_NODE,
            PREPARE_RESPONSE_NODE,
        )

        workflow.add_conditional_edges(
            TRANSFER_AGENT_NODE,
            self.route_transfer_agent_to_tools,
            list(get_args(TRANSFER_AGENT_ROUTE)),
        )

        workflow.add_edge(
            TRANSFER_AGENT_TOOLS_NODE,
            TRANSFER_AGENT_NODE,
        )

        """SETTING UP THE TERM DEPOSIT AGENT"""
        workflow.add_node(
            ENTER_TERM_DEPOSIT_CONTROLLER_NODE,
            controller_enter_node(
                assistant_name=ToTermDepositAgent.__name__,
                controller=TERM_DEPOSIT_CONTROLLER_NODE,
            ),
        )

        workflow.add_node(
            TERM_DEPOSIT_CONTROLLER_NODE,
            TermDepositController(
                prompt_srv=self.prompt_srv,
                llm=self.llm,
            ),
        )

        workflow.add_edge(
            ENTER_TERM_DEPOSIT_CONTROLLER_NODE,
            TERM_DEPOSIT_CONTROLLER_NODE,
        )

        workflow.add_node(
            TERM_DEPOSIT_CONTROLLER_TOOLS_NODE,
            create_tool_node_with_fallback(TERM_DEPOSIT_CONTROLLER_TOOLS),
        )

        workflow.add_node(
            ENTER_TERM_DEPOSIT_SUBGRAPH_NODE,
            subgraph_enter_node(ENTER_TERM_DEPOSIT_SUBGRAPH_NAME),
        )

        workflow.add_node(
            TERM_DEPOSIT_WORKFLOW_NODE,
            await wrap_agent_node(
                (await TermDepositGraph().get_workflow()).compile(),
                AssistantStateFields.TERM_DEPOSIT_AGENT_STATE,
            ),
        )

        workflow.add_edge(
            ENTER_TERM_DEPOSIT_SUBGRAPH_NODE,
            TERM_DEPOSIT_WORKFLOW_NODE,
        )
        workflow.add_edge(
            TERM_DEPOSIT_WORKFLOW_NODE,
            PREPARE_RESPONSE_NODE,
        )

        workflow.add_conditional_edges(
            TERM_DEPOSIT_CONTROLLER_NODE,
            self.route_term_deposit_controller_to_tools,
            {
                PREPARE_RESPONSE_NODE: PREPARE_RESPONSE_NODE,
                RETURN_CONTROL_NODE: RETURN_CONTROL_NODE,
                ENTER_TERM_DEPOSIT_SUBGRAPH_NODE: ENTER_TERM_DEPOSIT_SUBGRAPH_NODE,
                TERM_DEPOSIT_CONTROLLER_TOOLS_NODE: TERM_DEPOSIT_CONTROLLER_TOOLS_NODE,
            },
        )

        workflow.add_edge(
            TERM_DEPOSIT_CONTROLLER_TOOLS_NODE,
            TERM_DEPOSIT_CONTROLLER_NODE,
        )

        """SETTING UP THE CARD AGENT"""
        workflow.add_node(
            ENTER_CARD_CONTROLLER_NODE,
            controller_enter_node(
                assistant_name=ToCardAgent.__name__,
                controller=CARD_CONTROLLER_NODE,
            ),
        )

        workflow.add_node(
            CARD_CONTROLLER_NODE,
            CardController(
                prompt_srv=self.prompt_srv,
                llm=self.llm,
            ),
        )

        workflow.add_edge(
            ENTER_CARD_CONTROLLER_NODE,
            CARD_CONTROLLER_NODE,
        )

        workflow.add_node(
            CARD_CONTROLLER_TOOLS_NODE,
            create_tool_node_with_fallback(CARD_CONTROLLER_TOOLS),
        )

        workflow.add_node(
            ENTER_CARD_SUBGRAPH_NODE,
            subgraph_enter_node(ENTER_CARD_SUBGRAPH_NAME),
        )

        workflow.add_node(
            CARD_WORKFLOW_NODE,
            await wrap_agent_node(
                (await CardGraph().get_workflow()).compile(),
                AssistantStateFields.CARD_AGENT_STATE,
            ),
        )

        workflow.add_edge(
            ENTER_CARD_SUBGRAPH_NODE,
            CARD_WORKFLOW_NODE,
        )
        workflow.add_edge(
            CARD_WORKFLOW_NODE,
            PREPARE_RESPONSE_NODE,
        )

        workflow.add_conditional_edges(
            CARD_CONTROLLER_NODE,
            self.route_card_controller_to_tools,
            {
                PREPARE_RESPONSE_NODE: PREPARE_RESPONSE_NODE,
                RETURN_CONTROL_NODE: RETURN_CONTROL_NODE,
                ENTER_CARD_SUBGRAPH_NODE: ENTER_CARD_SUBGRAPH_NODE,
                CARD_CONTROLLER_TOOLS_NODE: CARD_CONTROLLER_TOOLS_NODE,
            },
        )

        workflow.add_edge(
            CARD_CONTROLLER_TOOLS_NODE,
            CARD_CONTROLLER_NODE,
        )

        """SETTING UP THE PRIMARY ASSISTANT"""

        workflow.add_node(
            PRIMARY_ASSISTANT_NODE,
            Assistant(
                prompt_srv=self.prompt_srv,
                llm=self.llm,
            ),
        )
        workflow.add_node(
            PRIMARY_ASSISTANT_TOOLS_NODE,
            create_tool_node_with_fallback(PRIMARY_ASSISTANT_TOOLS),
        )

        workflow.add_conditional_edges(
            PRIMARY_ASSISTANT_NODE,
            self.route_primary_assistant_to_tools,
            list(get_args(PRIMARY_ASSISTANT_ROUTE)),
        )
        workflow.add_edge(
            PRIMARY_ASSISTANT_TOOLS_NODE,
            PRIMARY_ASSISTANT_NODE,
        )
        workflow.add_node(
            RETURN_CONTROL_NODE,
            controller_exit_node,
        )
        workflow.add_node(DELETE_OLD_MESSAGE_NODE, delete_message)
        workflow.add_edge(
            RETURN_CONTROL_NODE,
            DELETE_OLD_MESSAGE_NODE,
        )
        workflow.add_edge(
            DELETE_OLD_MESSAGE_NODE,
            PRIMARY_ASSISTANT_NODE,
        )

        workflow.add_conditional_edges(
            START,
            self.direct_workflow_router,
            list(get_args(DialogController)),
        )

        return workflow
