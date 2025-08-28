import pytest

from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY, USER_CHOICE_ID_KEY
from app.assistant_v2.term_deposit.graph.node.select_term_deposit_product import (
    select_term_deposit_product_func,
)
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.entity import TermDepositProduct, TermUnit


@pytest.mark.asyncio
async def test_select_term_deposit_product(agent_config):
    # Mock the state and config
    state = {
        TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS: {
            "td_product_1": TermDepositProduct(
                id="td_product_1",
                name="test term deposit product 1",
                interest_rate=1.25,
                term_number=6,
                term_unit=TermUnit("M"),
                minimum_required_balance=0,
                is_available=True,
                maturity_earn=0,
            ),
            "td_product_2": TermDepositProduct(
                id="td_product_2",
                name="test term deposit product 2",
                interest_rate=1.5,
                term_number=1,
                term_unit=TermUnit("Y"),
                minimum_required_balance=0,
                is_available=False,
                maturity_earn=0,
            ),
        }
    }
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})
    config_data[USER_CHOICE_ID_KEY] = "td_product_1"

    # Call the function
    output = await select_term_deposit_product_func(state, agent_config)

    # Assertions
    assert TermDepositAgentStateFields.MESSAGES in output
    assert (
        output[TermDepositAgentStateFields.MESSAGES][0].content
        == "Selected term deposit product: test term deposit product 1"
    )
    assert TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS in output
    assert (
        list(output[TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS].values())[0].id
        == "td_product_1"
    )
    assert TermDepositAgentStateFields.RESUME_NODE in output
    assert output[TermDepositAgentStateFields.RESUME_NODE] is None


@pytest.mark.asyncio
async def test_select_account_no_choice(agent_config):
    # Mock the state and config
    state = {
        TermDepositAgentStateFields.TERM_DEPOSIT_PRODUCTS: {
            "td_product_1": TermDepositProduct(
                id="td_product_1",
                name="test term deposit product 1",
                interest_rate=1.25,
                term_number=6,
                term_unit=TermUnit("M"),
                minimum_required_balance=0,
                is_available=False,
                maturity_earn=0,
            ),
        }
    }
    config_data = agent_config.get(CONFIGURABLE_CONTEXT_KEY, {})
    config_data[USER_CHOICE_ID_KEY] = ""

    # Call the function and expect an assertion error
    with pytest.raises(AssertionError, match="User choice is empty"):
        await select_term_deposit_product_func(state, agent_config)
