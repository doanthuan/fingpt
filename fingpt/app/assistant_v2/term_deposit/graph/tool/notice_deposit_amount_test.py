import pytest

from app.assistant_v2.term_deposit.graph.tool.notice_deposit_amount import (
    _notice_deposit_amount,
)


@pytest.mark.asyncio
async def test_notice_deposit_amount_success():
    amount = 100.0
    result = await _notice_deposit_amount(amount)
    assert result == str(amount)


@pytest.mark.asyncio
async def test_notice_deposit_amount_zero():
    amount = 0.0
    result = await _notice_deposit_amount(amount)
    assert result == str(amount)


@pytest.mark.asyncio
async def test_notice_transfer_amount_negative():
    amount = -100.0
    with pytest.raises(ValueError):
        await _notice_deposit_amount(amount)
