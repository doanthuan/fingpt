import timeit
from typing import Any

from app.assistant_v2.primary.assistant import Assistant
from app.core.context import RequestContext
from app.prompt.prompt_module import PromptModule

module = PromptModule()


async def call_api(
    prompt: str,
    options: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    messages = context["vars"].get("messages", None)

    prompt_name = prompt.split(":")[0]
    prompt_label = prompt.split(":")[1]

    agent = await Assistant.build_agent(
        RequestContext(""),
        module.prompt_srv(),
        prompt_name,
        prompt_label,
    )

    start = timeit.default_timer()
    result = await agent.ainvoke(
        {
            "messages": messages,
        },
        temperature=0.01,
    )
    stop = timeit.default_timer()

    return {
        "output": {
            "content": result.content,
            "tool_calls": result.tool_calls,
            "time": stop - start,
            "token_use": result.usage_metadata,
        }
    }


async def call_api_with_cache(
    prompt: str,
    options: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    messages = context["vars"].get("messages", None)
    prompt_name = prompt.split(":")[0]
    prompt_label = prompt.split(":")[1]

    agent = await Assistant.build_agent(
        RequestContext(""),
        module.prompt_srv(),
        prompt_name,
        prompt_label,
    )

    start = timeit.default_timer()

    result = await agent.ainvoke(
        {
            "messages": messages,
        },
        temperature=0.0,
    )
    stop = timeit.default_timer()

    return {
        "output": {
            "content": result.content,
            "tool_calls": result.tool_calls,
            "time": stop - start,
            "token_use": result.usage_metadata,
        }
    }
