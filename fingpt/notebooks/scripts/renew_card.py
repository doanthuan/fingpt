# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.7
#   kernelspec:
#     display_name: fingpt-py3.11
#     language: python
#     name: fingpt-py3.11
# ---

# %%
from app.assistant.card.nodes import _build_choices_from_card_list
import logging
from uuid import uuid4
from pprint import pprint
from typing import Literal
from typing import Annotated, Any


from app.auth.auth_service import AuthService
from langchain_core.messages import HumanMessage, AIMessage
from app.core.config import settings
from app.core.context import RequestContext
from app.entity.api import AuthReqDto, AuthRespDto, AuthUserType
from app.prompt.prompt_service import PromptService
from app.assistant.card.state import CardAgentState
from app.assistant.card.nodes import retrieve_cards, retrieve_renewable_cards
from app.entity import (
    Card,
    ChatRespDto,
    ChatRespAction,
    ChatRespMetadataForCardChoice,
    ChatRespMetadataForChoices,
)

from app.entity.chat_response import ChatRespMetadataForRenewCard

from dotenv import load_dotenv
from IPython.display import Image, display
from langchain_core.messages import SystemMessage
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import END, StateGraph
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import InjectedState

# %%
ps = PromptService()

# %%
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

load_dotenv()

# %%
request_context = RequestContext(str(uuid4()))

# %%
llm_model = AzureChatOpenAI(azure_deployment=settings.azure_openai_deployment)

# %%
state_storage = "../data/renew_card.sqlite"
amemory = AsyncSqliteSaver.from_conn_string(state_storage)

# %% [markdown]
# # State

# %%
card_agent_state = CardAgentState(
    messages=[],
    responses=[],
    cards=None,
)

# %% [markdown]
# # Get cards


# %%
async def get_auth_response() -> AuthRespDto:
    auth_req_dto = AuthReqDto(
        username=settings.ebp_test_account_username,
        password=settings.ebp_test_account_password,
        user_type=AuthUserType.RETAIL,
    )
    auth_service = AuthService()
    auth_resp_dto = await auth_service.login(ctx=request_context, req=auth_req_dto)
    return auth_resp_dto


# %%
auth_response = await get_auth_response()

# %%
agent_configurable = {
    "ebp_access_token": auth_response.access_token,
    "ebp_cookie": auth_response.cookie,
    "ebp_edge_domain": auth_response.edge_domain,
    "ctx": request_context,
    "llm_model": llm_model,
    "ps": ps,
}

# %%
cards = await retrieve_cards.ainvoke(
    input={"state": card_agent_state},
    config={"configurable": agent_configurable | {"thread_id": str(uuid4())}},
)

# %%
for card in cards:
    pprint(card.dict())

# %%
retrieve_cards.get_input_schema().schema()

# %%
retrieve_cards.tool_call_schema.schema()

# %%
renewable_cards = await retrieve_renewable_cards.arun(
    tool_input={"state": card_agent_state},
    config={"configurable": agent_configurable | {"thread_id": str(uuid4())}},
)

# %%
retrieve_renewable_cards.get_input_schema().schema()

# %%
retrieve_cards.tool_call_schema.schema()

# %%
llm_model_with_tools = llm_model.bind_tools([retrieve_cards, retrieve_renewable_cards])


# %% [markdown]
# # Agent


# %%
def route_tools(
    state: CardAgentState,
) -> Literal["retrieve_cards", "retrieve_renewable_cards", "__end__"]:
    """Route the tools."""
    next_node = tools_condition(state["messages"])

    if next_node == END:
        return "__end__"

    ai_message = state["messages"][-1]
    tool_call = ai_message.tool_calls[0]  # type: ignore # noqa: PGH003

    return tool_call.get("name", "__end__")


# %%
system_message_content = """You are a helpful banking card assistant.
You can use retrieve_cards tool to get all cards that the user has, and retrieve_renewable_cards tool to get all cards that are expired or nearly expired.
If the user requests other things than card, then say that you can only help with the cards."""


# %%
def call_model(state: CardAgentState):
    messages = state["messages"]
    system_message = SystemMessage(content=system_message_content)
    messages = [system_message, *messages]
    response = llm_model_with_tools.invoke(messages)
    return {"messages": [response]}


# %%
def update_state(state: CardAgentState) -> dict[str, Card]:
    messages = state["messages"]
    tool_call_content = eval(messages[-1].content)
    card_dict = {card.id: card for card in tool_call_content}

    return {"cards": card_dict}


# %%


def available_renewable_card(
    state: CardAgentState, config: RunnableConfig
) -> dict[str, Any]:
    agent_config = config["configurable"]
    message = "I found the following cards that are renewable. Which one do you want to renew?"

    response = ChatRespDto(
        action=ChatRespAction.SHOW_CHOICES,
        thread_id=agent_config["thread_id"],
        response=message,
        metadata=_build_choices_from_card_list(state["cards"]),
    )

    return {
        "responses": [response.model_dump_json()],
        "messages": [AIMessage(content=message)],
    }


def no_available_renewable_card(
    state: CardAgentState,
    config: RunnableConfig,
) -> dict[str, Any]:
    agent_config = config["configurable"]
    message = "I didn't find any renewable card from your profile."

    response = ChatRespDto(
        action=ChatRespAction.SHOW_REPLY,
        thread_id=agent_config["thread_id"],
        response=message,
        metadata=None,
    )

    return {
        "responses": [response.model_dump_json()],
        "messages": [AIMessage(content=message)],
    }


def branch_retrieve_renewable_cards(state: CardAgentState):
    cards = state["cards"]

    if len(cards) == 0:
        return "no_available_renewable_card"

    return "available_renewable_card"


# %%
def renewable_card_choice(
    state: CardAgentState,
    config: RunnableConfig,
) -> dict[str, Any]:
    return {}


# %%
def review_renewable_card_info(
    state: CardAgentState,
    config: RunnableConfig,
) -> dict[str, Any]:
    agent_config = config["configurable"]
    message = "Let's review your renewable card info!"

    card = list(state["cards"].values())[0]

    response = ChatRespDto(
        action=ChatRespAction.RENEW_CARD,
        thread_id=agent_config["thread_id"],
        response=message,
        metadata=ChatRespMetadataForRenewCard(
            card=card.dict(),
        ),
    )

    return {
        "responses": [response.model_dump_json()],
        "messages": [AIMessage(content=message)],
    }


# %%
workflow = StateGraph(CardAgentState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("retrieve_cards", ToolNode([retrieve_cards]))
workflow.add_node("retrieve_renewable_cards", ToolNode([retrieve_renewable_cards]))
workflow.add_node("update_state", update_state)
workflow.add_node("available_renewable_card", available_renewable_card)
workflow.add_node("no_available_renewable_card", no_available_renewable_card)
workflow.add_node("renewable_card_choice", renewable_card_choice)
workflow.add_node("review_renewable_card_info", review_renewable_card_info)


workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    source="agent",
    path=route_tools,
)

workflow.add_edge("retrieve_cards", "agent")
# workflow.add_edge("retrieve_renewable_cards", "agent")
workflow.add_edge("retrieve_renewable_cards", "update_state")
workflow.add_conditional_edges(
    source="update_state",
    path=branch_retrieve_renewable_cards,
    path_map={
        "available_renewable_card": "available_renewable_card",
        "no_available_renewable_card": "no_available_renewable_card",
    },
)
workflow.add_edge("available_renewable_card", "renewable_card_choice")
workflow.add_edge("no_available_renewable_card", "__end__")
workflow.add_edge("renewable_card_choice", "review_renewable_card_info")
workflow.add_edge("review_renewable_card_info", "__end__")

graph = workflow.compile(
    checkpointer=amemory, interrupt_before=["renewable_card_choice"]
)

# %%
display(Image(graph.get_graph().draw_mermaid_png()))

# %%
thread_id = str(uuid4())
config = {"configurable": {"thread_id": thread_id} | agent_configurable}

# %%
input_message = "how many cards do i have?"
async for event in graph.astream(
    {"messages": [input_message]}, config, stream_mode="values"
):
    event["messages"][-1].pretty_print()

# %%
input_message = "I wanna renew my card"
async for event in graph.astream(
    {"messages": [input_message]}, config, stream_mode="values"
):
    event["messages"][-1].pretty_print()

# %%
input_message = "renew the cards that will be expired in next 4 years"
async for event in graph.astream(
    {"messages": [input_message]}, config, stream_mode="values"
):
    event["messages"][-1].pretty_print()

# %%
current_state = await graph.aget_state(config=config)
nearly_last_card_id = list(current_state.values.get("cards"))[-1]
print(nearly_last_card_id)

# %%
cards = current_state.values.get("cards")
print(cards)

# %%
await graph.aupdate_state(
    config=config,
    values={
        "cards": {nearly_last_card_id: cards[nearly_last_card_id]},
        "messages": HumanMessage(content=cards[nearly_last_card_id].card_type),
    },
    as_node="renewable_card_choice",
)

# %%
current_state = await graph.aget_state(config=config)
print(current_state.values)

# %%
current_state = await graph.aget_state(config=config)
print(current_state)

# %%
print(current_state.values["responses"])

# %%
cards = current_state.values.get("cards")
print(cards)

# %%
nearly_last_card_id = list(current_state.values.get("cards"))[-1]
print(nearly_last_card_id)

# %%
await graph.aupdate_state(
    config=config,
    values={
        "cards": {nearly_last_card_id: cards[nearly_last_card_id]},
        "messages": HumanMessage(content=cards[nearly_last_card_id].card_type),
    },
    as_node="renewable_card_choice",
)

# %%
current_state = await graph.aget_state(config=config)
print(current_state.values)


# %%
# Continue the graph execution
async for event in graph.astream(None, config, stream_mode="values"):
    event["messages"][-1].pretty_print()

# %%
input_message = "it's too hot now, what is the weather in HCMC?"
async for event in graph.astream(
    {"messages": [input_message]}, config, stream_mode="values"
):
    event["messages"][-1].pretty_print()

# %%
current_state = await graph.aget_state(config=config)
print(current_state.values)
