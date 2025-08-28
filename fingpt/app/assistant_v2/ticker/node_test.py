from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    PROMPT_SERVICE_KEY,
)
from app.assistant_v2.ticker.node import income_stmt_analyst
from app.assistant_v2.ticker.state import TickerAgentStateFields


@pytest.mark.asyncio
async def test_income_stmt_analyst_success():
    mock_prompt_service = AsyncMock()
    mock_prompt_service.get_prompt.return_value = AsyncMock(
        tmpl=MagicMock(), llm_model=MagicMock()
    )
    mock_chain = AsyncMock()
    mock_chain.ainvoke.return_value = "Income statement analysis report"
    mock_prompt_service.get_prompt.return_value.tmpl.__or__.return_value.__or__.return_value = (
        mock_chain
    )

    with patch(
        "app.assistant_v2.ticker.node.PromptService", return_value=mock_prompt_service
    ):
        config = {
            CONFIGURABLE_CONTEXT_KEY: {
                PROMPT_SERVICE_KEY: mock_prompt_service,
                CONTEXT_KEY: AsyncMock(logger=MagicMock()),
            }
        }
        state = {
            TickerAgentStateFields.INCOME_STMT: "income statement data",
            TickerAgentStateFields.COMPANY_INFO: {"industry": "tech"},
            TickerAgentStateFields.SECTION_7: "section 7 text",
        }
        result = await income_stmt_analyst(state, config)
        assert result[TickerAgentStateFields.MESSAGES] == [
            "Income statement analysis report"
        ]
        assert (
            result[TickerAgentStateFields.INCOME_STMT_REPORT]
            == "Income statement analysis report"
        )


@pytest.mark.asyncio
async def test_income_stmt_analyst_failure():
    mock_prompt_service = AsyncMock()
    mock_prompt_service.get_prompt.side_effect = Exception("Prompt service error")

    with patch(
        "app.assistant_v2.ticker.node.PromptService", return_value=mock_prompt_service
    ):
        config = {
            CONFIGURABLE_CONTEXT_KEY: {
                PROMPT_SERVICE_KEY: mock_prompt_service,
                CONTEXT_KEY: AsyncMock(logger=MagicMock()),
            }
        }
        state = {
            TickerAgentStateFields.INCOME_STMT: "income statement data",
            TickerAgentStateFields.COMPANY_INFO: {"industry": "tech"},
            TickerAgentStateFields.SECTION_7: "section 7 text",
        }
        with pytest.raises(Exception, match="Prompt service error"):
            await income_stmt_analyst(state, config)
