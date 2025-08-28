from typing import Any, cast

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    RemoveMessage,
    ToolCall,
    ToolMessage,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.config import RunnableConfig
from langgraph.errors import GraphInterrupt
from langgraph.graph.state import CompiledStateGraph

from app.assistant_v2.common.base_agent_state import BaseAgentState
from app.assistant_v2.constant import (
    CONFIGURABLE_CONTEXT_KEY,
    CONTEXT_KEY,
    LAST_SUMMARY_MESSAGE_ID_KEY,
    PENDING_RESPONSE_KEY,
    PROMPT_SERVICE_KEY,
    USER_CHOICE_ID_KEY,
    USER_QUERY_KEY,
)
from app.assistant_v2.primary.constant import (
    CONTROLLER_ENTER_CONTENT,
    CONTROLLER_EXIT_WITH_SUMMARY,
    SUBGRAPH_ENTER_CONTENT,
    TICKER_AGENT_NODE,
    DialogController,
)
from app.assistant_v2.primary.state import (
    AssistantConfig,
    AssistantState,
    AssistantStateFields,
    agent_state_key_map,
)
from app.core.config import settings
from app.core.context import RequestContext
from app.entity.assistant import AssistantStatus
from app.entity.error import InterruptionNotAllowedError, MissingConfigDataError
from app.prompt.prompt_service import PromptService
from app.utils.modified_langfuse_decorator import observe  # type: ignore


def controller_enter_node(
    assistant_name: str,
    controller: DialogController,
):
    def node(
        state: AssistantState,
        config: RunnableConfig,
    ) -> dict[str, Any]:
        messages = state[AssistantStateFields.MESSAGES]
        tool_calls = messages[-1].tool_calls  # type: ignore

        new_messages = []
        if tool_calls:
            # get first tool which is same as assistant_name
            selected_tool = [
                cast(ToolCall, tool)
                for tool in tool_calls  # type: ignore
                if tool["name"] == assistant_name
            ][0]
            new_messages.append(  # type: ignore
                ToolMessage(
                    content=CONTROLLER_ENTER_CONTENT.format(agent=controller),
                    name=selected_tool["name"],
                    tool_call_id=selected_tool["id"],
                )
            )

        current_stack = state.get(AssistantStateFields.CONTROLLER_STACK, []) or []
        current_stack.append(controller)

        return {
            AssistantStateFields.MESSAGES: new_messages,
            AssistantStateFields.CONTROLLER_STACK: current_stack,
        }

    return node


def _get_last_summary_message_id(config_data: AssistantConfig):
    if LAST_SUMMARY_MESSAGE_ID_KEY not in config_data:
        config_data[LAST_SUMMARY_MESSAGE_ID_KEY] = []
        return None
    return config_data[LAST_SUMMARY_MESSAGE_ID_KEY].pop()


def _set_last_summary_message_id(config_data: AssistantConfig, message_id: str):
    if LAST_SUMMARY_MESSAGE_ID_KEY not in config_data:
        config_data[LAST_SUMMARY_MESSAGE_ID_KEY] = []
    config_data[LAST_SUMMARY_MESSAGE_ID_KEY].append(message_id)


async def _summary_previous_messages(
    state: BaseAgentState,
    config: RunnableConfig,
) -> AIMessage:
    """
    Summarize the previous messages for the user.
    """
    config_data: AssistantConfig = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    last_summary_message_id = state.get(AssistantStateFields.LAST_SUMMARY_MESSAGE_ID)
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()
    logger.info(f"Summarizing previous messages from {last_summary_message_id}...")

    messages = state.get(AssistantStateFields.MESSAGES, [])
    need_summary_messages = []
    for message in messages[::-1][2:]:  # skip last HumanMessage and last AIMessage
        if message.id == last_summary_message_id:
            break
        if isinstance(message, AIMessage) and not message.tool_calls:
            need_summary_messages.append(f"AI: {message.content}")
        if isinstance(message, HumanMessage):
            need_summary_messages.append(f"User: {message.content}")
    need_summary_messages_str = "\n".join(need_summary_messages[::-1])

    prompt_service: PromptService = config_data[PROMPT_SERVICE_KEY]
    prompt = await prompt_service.get_prompt(
        ctx=ctx,
        name=settings.assistant_primary_summarize_messages_prompt,
        label=settings.assistant_primary_summarize_messages_label,
        type="chat",
    )
    prompt_tmpl = prompt.tmpl + ChatPromptTemplate.from_messages(
        [
            ("user", "This is the conversation: {messages}"),
        ]
    )
    chain = prompt_tmpl | prompt.llm_model
    response = await chain.ainvoke(
        input={
            "messages": need_summary_messages_str,
        },
        config=config,
    )
    logger.debug(
        f"Summary {len(need_summary_messages)} messages to new message: {response}"
    )
    return response


def _extract_two_last_messages(state: AssistantState):
    messages = state[AssistantStateFields.MESSAGES]
    two_last_messages = []
    for message in messages[-2:]:
        if isinstance(message, AIMessage):
            two_last_messages.append(
                AIMessage(
                    content=message.content,
                    tool_calls=message.tool_calls,
                )
            )
        if isinstance(message, HumanMessage):
            two_last_messages.append(HumanMessage(message.content))

    return two_last_messages


@observe()
async def controller_exit_node(
    state: AssistantState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """
    Pop the controller stack to return the control to the primary assistant.
    """
    config_data: AssistantConfig = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()

    new_messages = []
    # Summarize the previous messages

    new_messages.append(HumanMessage(content=config_data[USER_QUERY_KEY]))

    current_stack = state.get(AssistantStateFields.CONTROLLER_STACK, [])
    if current_stack:
        controller = current_stack.pop()
        summary_message = await _summary_previous_messages(state, config)
        last_two_messages = _extract_two_last_messages(state)
        new_messages = [summary_message] + last_two_messages
        last_tool_call = new_messages[-1].tool_calls[-1]  # type: ignore
        new_messages += [
            ToolMessage(
                CONTROLLER_EXIT_WITH_SUMMARY.format(
                    agent=controller, reason=last_tool_call["args"].get("reason", "")
                ),
                name=last_tool_call["name"],
                tool_call_id=last_tool_call["id"],
            )
        ]
        logger.info(f"Exiting and clearing the state for agent: {controller}")
        if controller in agent_state_key_map:
            agent_state_key = agent_state_key_map[controller]
            return {
                AssistantStateFields.MESSAGES: new_messages,
                AssistantStateFields.CONTROLLER_STACK: current_stack,
                agent_state_key: {},
                AssistantStateFields.LAST_SUMMARY_MESSAGE_ID: summary_message.id,
            }
        if controller == TICKER_AGENT_NODE:
            return {
                AssistantStateFields.MESSAGES: new_messages,
                AssistantStateFields.CONTROLLER_STACK: current_stack,
                AssistantStateFields.LAST_SUMMARY_MESSAGE_ID: summary_message.id,
            }

    return {
        AssistantStateFields.MESSAGES: new_messages,
        AssistantStateFields.CONTROLLER_STACK: current_stack,
        AssistantStateFields.LAST_SUMMARY_MESSAGE_ID: None,
    }


def prepare_response_node(
    state: AssistantState,
    config: RunnableConfig,
):
    """
    Moving the pending response to be returned
    """
    config_data: AssistantConfig = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()
    logger.info("Preparing response...")
    logger.debug(f"Config data {config_data['pending_response']}")
    assert config_data[PENDING_RESPONSE_KEY], MissingConfigDataError(
        "Missing expected response"
    )
    return dict(state)


def subgraph_enter_node(
    subgraph_name: str,
):
    """
    We are using tool-calling to enter subgraph, so we need this node for setting up the state.
    """

    def node(
        state: AssistantState,
        config: RunnableConfig,
    ) -> dict[str, Any]:
        messages = state[AssistantStateFields.MESSAGES]
        tool_calls = messages[-1].tool_calls  # type: ignore

        new_messages = []
        if tool_calls:
            new_messages.append(  # type: ignore
                ToolMessage(
                    content=SUBGRAPH_ENTER_CONTENT.format(agent=subgraph_name),
                    name=tool_calls[0]["name"],
                    tool_call_id=tool_calls[0]["id"],
                )
            )

        return {
            AssistantStateFields.MESSAGES: new_messages,
        }

    return node


def _get_last_not_tool_call_message(messages):
    last_messages = []
    for message in messages:
        if isinstance(message, AIMessage) and not message.tool_calls:
            last_messages.append(message)
        if isinstance(message, HumanMessage):
            last_messages.append(message)
    return last_messages


async def wrap_agent_node(
    agent: CompiledStateGraph,
    agent_state_key: str,
):
    """
    Wrapping the agent graph to be used as a subgraph.
    """

    @observe()
    async def node(
        state: AssistantState,
        config: RunnableConfig,
    ) -> dict[str, Any]:
        config_data: AssistantConfig = config.get(CONFIGURABLE_CONTEXT_KEY, {})
        ctx: RequestContext = config_data[CONTEXT_KEY]
        logger = ctx.logger()
        logger.info("Running agent subgraph ...")
        agent_state = state.get(agent_state_key, {}) or {}

        if (
            config_data.get(USER_QUERY_KEY, None) is not None
            and len(str(config_data[USER_QUERY_KEY])) > 0
        ):
            user_query = HumanMessage(str(config_data[USER_QUERY_KEY]))
            if (
                AssistantStateFields.MESSAGES not in agent_state
                or not agent_state[AssistantStateFields.MESSAGES]
            ):
                agent_state[AssistantStateFields.MESSAGES] = (
                    _get_last_not_tool_call_message(
                        state[AssistantStateFields.MESSAGES]
                    )
                )
            else:
                agent_state[AssistantStateFields.MESSAGES].append(user_query)

        if (
            config_data.get(USER_CHOICE_ID_KEY, None) is not None
            and len(str(config_data[USER_CHOICE_ID_KEY])) > 0
        ):
            user_choice = HumanMessage("I have made my choice.")
            if (
                AssistantStateFields.MESSAGES not in agent_state
                or not agent_state[AssistantStateFields.MESSAGES]
            ):
                agent_state[AssistantStateFields.MESSAGES] = [user_choice]
            else:
                agent_state[AssistantStateFields.MESSAGES].append(user_choice)

        try:
            new_state = await agent.ainvoke(
                agent_state,
                config=config,
                stream_mode="values",
            )

        except GraphInterrupt:
            logger.debug("Graph interrupted for HITL...")
            raise InterruptionNotAllowedError("Interrupt not allowed for subgraph")

        logger.info("Subgraph completed successfully")

        status = AssistantStatus.WAIT_FOR_QUERY
        if (
            AssistantStateFields.RESUME_NODE in new_state
            and new_state[AssistantStateFields.RESUME_NODE]
        ):
            status = AssistantStatus.WAIT_FOR_CHOICE

        new_messages = new_state.get(AssistantStateFields.MESSAGES, [])
        return {
            AssistantStateFields.MESSAGES: [new_messages[-1]] if new_messages else [],
            AssistantStateFields.STATUS: status,
            agent_state_key: new_state,
        }

    return node


async def delete_message(
    state: AssistantState, config: RunnableConfig
) -> dict[str, Any]:
    """
    Delete the last message from the state.
    """
    messages = state[AssistantStateFields.MESSAGES]
    deleted_messages = []
    last_message_id = state.get(AssistantStateFields.LAST_SUMMARY_MESSAGE_ID)
    if not state.get(AssistantStateFields.CONTROLLER_STACK):
        for message in messages:
            if message.id == last_message_id:
                break
            deleted_messages.append(RemoveMessage(id=message.id))
        return {
            AssistantStateFields.MESSAGES: deleted_messages,
        }
    else:
        return {
            AssistantStateFields.MESSAGES: [],
        }
