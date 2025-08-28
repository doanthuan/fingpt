import json
from unittest.mock import AsyncMock, patch

import pytest

from app.assistant_v2.term_deposit.graph.tool.get_term_deposit_products import (
    _get_term_deposit_products,
)
from app.assistant_v2.term_deposit.state import TermDepositAgentStateFields
from app.entity import TermDepositProduct, TermUnit


@pytest.mark.asyncio
async def test_get_term_deposit_products_success(agent_config):
    # Mock the list_td_products function
    term_deposit_products = [
        TermDepositProduct(
            id="td_product_1",
            name="test term deposit product 1",
            interest_rate=1.25,
            term_number=6,
            term_unit=TermUnit("M"),
            minimum_required_balance=0,
            is_available=True,
            maturity_earn=0,
        ),
        TermDepositProduct(
            id="td_product_2",
            name="test term deposit product 2",
            interest_rate=1.5,
            term_number=1,
            term_unit=TermUnit("Y"),
            minimum_required_balance=0,
            is_available=False,
            maturity_earn=0,
        ),
    ]
    mock_products = AsyncMock(return_value=term_deposit_products)
    state = {
        TermDepositAgentStateFields.TERM_UNIT: "M",
        TermDepositAgentStateFields.TERM_NUMBER: 6,
    }
    with patch(
        "app.assistant_v2.term_deposit.graph.tool.get_term_deposit_products.list_td_products",
        mock_products,
    ):
        result = await _get_term_deposit_products(5000, agent_config, state)

        # Assertions
        result_list = eval(result)
        result_products = [
            TermDepositProduct(**json.loads(product)) for product in result_list
        ]
        assert result_products == [term_deposit_products[0]]


@pytest.mark.asyncio
async def test_get_term_deposit_products_failure(agent_config):
    # Mock the list_td_products function to raise an exception
    with patch(
        "app.assistant_v2.term_deposit.graph.tool.get_term_deposit_products.list_td_products",
        side_effect=Exception("API error"),
    ):
        # Call the function and expect an exception
        with pytest.raises(Exception, match="API error"):
            await _get_term_deposit_products(5000, agent_config, {})
