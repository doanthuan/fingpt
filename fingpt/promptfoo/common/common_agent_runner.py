import uuid
from typing import Any, Awaitable, Callable

from langchain_openai import AzureChatOpenAI

from app.core.context import RequestContext
from app.prompt.prompt_module import PromptModule

module = PromptModule()


async def generic_agent_router(
    prompt: str,
    options: dict[str, Any],
    context: dict[str, Any],
    build_agent_func: Callable[[RequestContext, Any, Any, str, str], Awaitable[Any]],
) -> dict[str, Any]:
    messages = context["vars"].get("messages", None)
    prompt_name, prompt_label = prompt.split(":")

    agent = await build_agent_func(
        RequestContext(""),
        module.prompt_srv(),
        prompt_name,
        prompt_label,
    )

    result = await agent.ainvoke(
        {"messages": messages},
        temperature=0.0,
    )

    return {
        "output": {
            "content": result.content,
            "tool_calls": result.tool_calls,
        }
    }


async def common_call_api(
    prompt: str,
    options: dict[str, Any],
    context: dict[str, Any],
    state_class: Any,
    call_model_func: Callable,
) -> dict[str, Any]:
    messages = context["vars"].get("messages", None)

    model = options.get("config", {})["model"]
    llm = AzureChatOpenAI(azure_deployment=model)

    state = state_class(messages=messages)
    config = {
        "configurable": {
            "ctx": RequestContext("123"),
            "llm_model": llm,
            "ps": module.prompt_srv(),
            "thread_id": str(uuid.uuid4()),
            "pending_response": [],
        }
    }
    logger = RequestContext("123").logger()
    logger.info(f"Prompt: {prompt}")
    prompt_name, prompt_label = prompt.split(":")

    response = await call_model_func(
        state=state, config=config, prompt_name=prompt_name, prompt_label=prompt_label
    )

    logger.info(f"call model response {response.get('messages')[-1]}")
    result = response.get("messages")[-1]

    logger.debug(f"type result {type(result)}")

    return {
        "output": {
            "content": result.content,
            "tool_calls": result.tool_calls,
        }
    }
