import pytest

from app.assistant_v2.term_deposit.graph.tool.notice_term_number import (
    _notice_term_number,
)


@pytest.mark.asyncio
async def test_notice_term_number_success():
    term_number = 6
    result = await _notice_term_number(term_number)
    assert result == str(term_number)


@pytest.mark.asyncio
async def test_notice_deposit_amount_zero():
    term_number = 0
    result = await _notice_term_number(term_number)
    assert result == str(term_number)
