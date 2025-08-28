import pytest
from langchain_core.messages import HumanMessage

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, PENDING_RESPONSE_KEY
from app.assistant_v2.term_deposit.graph.node.present_offer import present_offer_func
from app.assistant_v2.term_deposit.graph.node.select_term_deposit_product import (
    select_term_deposit_product_node,
)
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.entity import TermDepositProduct, TermUnit


@pytest.mark.asyncio
async def test_present_offer(agent_config):
    # Mock the state and config
    state = {
        TermDepositAgentStateFields.MESSAGES: [HumanMessage(content="test message")],
        TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS: {
            "td_product_1": TermDepositProduct(
                id="td_product_1",
                name="test term deposit product 1",
                interest_rate=1.25,
                term_number=6,
                term_unit=TermUnit("M"),
                minimum_required_balance=0,
                is_available=True,
                maturity_earn=100,
            ),
            "td_product_2": TermDepositProduct(
                id="td_product_2",
                name="test term deposit product 2",
                interest_rate=1.5,
                term_number=1,
                term_unit=TermUnit("Y"),
                minimum_required_balance=0,
                is_available=True,
                maturity_earn=200,
            ),
        },
        TermDepositAgentStateFields.DEPOSIT_AMOUNT: 1000,
    }

    # Call the function
    output = await present_offer_func(state, agent_config)
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})

    # Assertions
    assert TermDepositAgentStateFields.RESUME_NODE in output
    assert (
        output[TermDepositAgentStateFields.RESUME_NODE]
        == select_term_deposit_product_node
    )
    assert len(config_data[PENDING_RESPONSE_KEY]) == 1
    assert config_data[PENDING_RESPONSE_KEY][0].action == "SHOW_CHOICES"
    assert len(config_data[PENDING_RESPONSE_KEY][0].metadata.choices) == 2
    assert config_data[PENDING_RESPONSE_KEY][0].metadata.choices[0].is_enabled
    assert config_data[PENDING_RESPONSE_KEY][0].metadata.choices[1].is_enabled
