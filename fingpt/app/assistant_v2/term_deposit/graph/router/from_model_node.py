from typing import Dict

from app.assistant_v2.common.base_graph import END_NODE, EdgeName, NodeName
from app.assistant_v2.term_deposit.graph.node.available_term_deposit_account import (
    available_term_deposit_account_node,
)
from app.assistant_v2.term_deposit.graph.node.available_term_deposit_product import (
    available_term_deposit_product_node,
)
from app.assistant_v2.term_deposit.graph.node.multiple_active_account_match import (
    multiple_active_account_match_node,
)
from app.assistant_v2.term_deposit.graph.node.review_term_deposit import (
    review_term_deposit_node,
)
from app.assistant_v2.term_deposit.graph.tool import tool_node
from app.assistant_v2.term_deposit.state import (
    TermDepositAgentState,
    TermDepositAgentStateFields,
)

to_review_edge = EdgeName("to_review")
to_select_account_edge = EdgeName("to_select_account")
to_select_term_deposit_account_edge = EdgeName("to_select_term_deposit_account")
to_select_term_deposit_product_edge = EdgeName("to_select_term_deposit_product")
to_tool_edge = EdgeName("to_tool")
to_end_edge = EdgeName("to_end")

router_map_from_model: Dict[EdgeName, NodeName] = {
    to_review_edge: review_term_deposit_node,
    to_select_term_deposit_account_edge: available_term_deposit_account_node,
    to_select_account_edge: multiple_active_account_match_node,
    to_select_term_deposit_product_edge: available_term_deposit_product_node,
    to_tool_edge: tool_node,
    to_end_edge: END_NODE,
}


def _router_to_hil(state: TermDepositAgentState) -> EdgeName:
    term_deposit_products = state.get(
        TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS, {}
    )
    term_deposit_accounts = state.get(
        TermDepositAgentStateFields.TERM_DEPOSIT_ACCOUNTS, {}
    )
    accounts = state.get(TermDepositAgentStateFields.ACTIVE_ACCOUNTS, {})
    deposit_amount = state.get(TermDepositAgentStateFields.DEPOSIT_AMOUNT, 0)
    human_approval_active_account = state.get(
        TermDepositAgentStateFields.HUMAN_APPROVAL_ACTIVE_ACCOUNT, False
    )
    human_approval_term_deposit_account = state.get(
        TermDepositAgentStateFields.HUMAN_APPROVAL_TERM_DEPOSIT_ACCOUNT, False
    )
    human_approval_term_deposit_product = state.get(
        TermDepositAgentStateFields.HUMAN_APPROVAL_TERM_DEPOSIT_PRODUCT, False
    )
    human_approval_present_offer = state.get(
        TermDepositAgentStateFields.HUMAN_APPROVAL_PRESENT_OFFER, False
    )

    print(f"TD product: {term_deposit_products}")
    print(f"Accounts: {accounts}")
    print(f"TD accounts: {term_deposit_accounts}")
    print(f"Deposit amount: {deposit_amount}")
    print(f"Human approval active account: {human_approval_active_account}")
    print(f"Human approval term deposit account: {human_approval_term_deposit_account}")
    print(f"Human approval term deposit product: {human_approval_term_deposit_product}")
    print(f"Human approval present offer: {human_approval_present_offer}")

    if len(term_deposit_accounts) > 0:
        available_term_deposit_accounts = [
            account.id
            for account in term_deposit_accounts.values()
            if account.is_renewable is True and account.is_mature is True
        ]
    else:
        available_term_deposit_accounts = []

    if len(term_deposit_products) > 0:
        available_term_deposit_products = [
            product.id
            for product in term_deposit_products.values()
            if product.is_available is True
        ]
    else:
        available_term_deposit_products = []

    if len(accounts) > 0:
        suffficient_balance_accounts = [
            account.id
            for account in accounts.values()
            if account.available_balance >= deposit_amount
        ]
    else:
        suffficient_balance_accounts = []

    if (
        len(accounts) == 1
        and len(term_deposit_products) == 1
        and human_approval_active_account
        and human_approval_term_deposit_product
        or len(term_deposit_accounts) == 1
        and len(term_deposit_products) == 1
        and human_approval_term_deposit_account
        and human_approval_term_deposit_product
        or len(term_deposit_accounts) == 1
        and len(term_deposit_products) == 1
        and human_approval_present_offer
    ):
        print("Next node: review")
        return to_review_edge

    if (
        len(available_term_deposit_accounts) == 1
        and len(term_deposit_accounts) == 1
        and human_approval_term_deposit_account
    ):
        if available_term_deposit_products:
            print("Next node: select_term_deposit_product")
            return to_select_term_deposit_product_edge
        else:
            print("Next node: end")
            return to_end_edge

    if available_term_deposit_accounts:
        print("Next node: select_term_deposit_account")
        return to_select_term_deposit_account_edge

    if (
        len(suffficient_balance_accounts) == 1
        and len(accounts) == 1
        and human_approval_active_account
    ):
        if available_term_deposit_products:
            print("Next node: select_term_deposit_product")
            return to_select_term_deposit_product_edge
        else:
            print("Next node: end")
            return to_end_edge

    if suffficient_balance_accounts:
        print("Next node: select_account")
        return to_select_account_edge

    print("Next node: end")
    return to_end_edge


def router_from_model(state: TermDepositAgentState) -> EdgeName:
    last_message = state[TermDepositAgentStateFields.MESSAGES][-1]
    if not last_message.tool_calls:
        return _router_to_hil(state)
    else:
        return to_tool_edge
