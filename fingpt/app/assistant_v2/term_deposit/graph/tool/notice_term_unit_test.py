import pytest

from app.assistant_v2.term_deposit.graph.tool.notice_term_unit import _notice_term_unit


@pytest.mark.asyncio
async def test_notice_term_number_success():
    term_unit = "M"
    result = await _notice_term_unit(term_unit)
    assert result == str(term_unit)
