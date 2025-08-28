from typing import Any

from app.assistant_v2.ticker.symbol_identifier_agent import SymbolIdentifierAgent
from promptfoo.common.common_agent_runner import generic_agent_router


async def ticker_agent_router(
    prompt: str,
    options: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    return await generic_agent_router(
        prompt, options, context, SymbolIdentifierAgent.build_agent
    )
