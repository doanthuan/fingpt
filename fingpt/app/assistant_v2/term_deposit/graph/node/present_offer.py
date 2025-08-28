from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langfuse.decorators import observe  # type: ignore

from app.assistant_v2.common.base_graph import NodeName
from app.assistant_v2.constant import PENDING_RESPONSE_KEY, THREAD_ID_KEY
from app.assistant_v2.term_deposit.graph.utils import (
    _build_choices_from_term_deposit_products,
    convert_to_time_string,
)
from app.assistant_v2.term_deposit.state import (
    TermDepositAgentState,
    TermDepositAgentStateFields,
)
from app.assistant_v2.util.misc import extract_config
from app.entity.chat_response import ChatRespAction, ChatRespDto

from .select_term_deposit_product import select_term_deposit_product_node

present_offer_node = NodeName("present_offer")


@observe()
async def present_offer_func(
    state: TermDepositAgentState,
    config: RunnableConfig,
) -> Dict[str, Any]:
    config_data, _, logger = extract_config(config)
    logger.info("Present available products")
    products = list(state[TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS].values())
    available_products = [product for product in products if product.is_available]

    max_maturity_product = max(
        available_products,
        key=lambda p: p.maturity_earn if p.maturity_earn else 0,
    )
    amount = float(state[TermDepositAgentStateFields.DEPOSIT_AMOUNT])
    term_unit_string = convert_to_time_string(max_maturity_product.term_unit)

    message = (
        f"We have a surprise for you! "
        f"We now offer a new {max_maturity_product.term_number} {term_unit_string} term "
        f"with a better interest rate of {max_maturity_product.interest_rate:.2f}% to maximize your earning."
        f" Your term deposit of ${'{:,.2f}'.format(amount)} is about to mature. "
        "Would you like to renew it with our new offer?"
    )

    response = ChatRespDto(
        action=ChatRespAction.SHOW_CHOICES,
        thread_id=config_data[THREAD_ID_KEY],
        response=message,
        metadata=_build_choices_from_term_deposit_products(
            state[TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS]
        ),
    )

    logger.info("Returning response...")
    config_data[PENDING_RESPONSE_KEY].append(response)
    if any([c.is_enabled for c in response.metadata.choices]):
        return {
            TermDepositAgentStateFields.MESSAGES: [AIMessage(content=message)],
            TermDepositAgentStateFields.RESUME_NODE: select_term_deposit_product_node,
        }
    return {}
