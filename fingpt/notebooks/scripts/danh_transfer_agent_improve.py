# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.7
#   kernelspec:
#     display_name: .venv
#     language: python
#     name: python3
# ---

# %%
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode
from langchain_core.runnables.config import RunnableConfig
import requests
import uuid
import os
from app.core.config import settings
import time

# %% [markdown]
# ## Aquire auth info

# %%
HOST = "https://app.stg.sdbxaz.azure.backbaseservices.com/api/fin-gpt"
LOGIN_API = "/v1/auth/login"
request_id = str(uuid.uuid4())
sanbox_key = os.environ.get("SANDBOX_API_KEY")
user_name = os.environ.get("EBP_TEST_ACCOUNT_USERNAME")
password = os.environ.get("EBP_TEST_ACCOUNT_PASSWORD")
header = {"x-request-id": request_id, "X-SDBXAZ-API-KEY": sanbox_key}
r = requests.post(
    HOST + LOGIN_API,
    headers=header,
    json={"username": user_name, "password": password, "user_type": "retail"},
)
result = r.json()
access_token = result.get("access_token")
cookie = result.get("cookie")
cookie, access_token

# %%
from langchain_openai import AzureChatOpenAI
from app.assistant.constant import (
    CONTEXT_KEY,
    EBP_ACCESS_TOKEN_KEY,
    EBP_COOKIE_KEY,
    EBP_EDGE_DOMAIN_KEY,
    LLM_MODEL_KEY,
    THREAD_ID_KEY,
)
from app.core.context import RequestContext


def get_config(thread_id, cookie, access_token):
    config = RunnableConfig(
        configurable={
            EBP_ACCESS_TOKEN_KEY: access_token,
            EBP_COOKIE_KEY: cookie,
            EBP_EDGE_DOMAIN_KEY: settings.ebp_edge_domain,
            THREAD_ID_KEY: thread_id,
            CONTEXT_KEY: RequestContext(thread_id),
            LLM_MODEL_KEY: AzureChatOpenAI(
                azure_deployment=settings.azure_openai_deployment
            ),
        }
    )
    return config


# %%
THREAD_ID = "thread_4"
config = get_config(THREAD_ID, cookie, access_token)

# %%
from typing import Annotated
from app.assistant.base_agent_config import extract_bb_retail_api_config
from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY
from app.assistant_v2.transfer.node import _filter_contact
from app.assistant_v2.transfer.state import TransferAgentStateFields
from app.entity.bb_api import BbQueryPaging
from langgraph.prebuilt import InjectedState
from app.bb_retail.request import list_contacts
from app.bb_retail.request import list_accounts
from app.entity.transfer import Contact


@tool
async def get_contact(
    reciepient_name: str, config: RunnableConfig, state: Annotated[dict, InjectedState]
):
    """Call to get list of user contact with have name as reciepient name"""
    config_data = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()
    logger.debug("Retrieving contact list...")
    api_config = extract_bb_retail_api_config(config_data)
    contacts = await list_contacts(
        ctx=ctx,
        config=api_config,
        params=BbQueryPaging(fr0m=0, size=500),
    )
    filtered_contact_list = _filter_contact(
        str(reciepient_name),
        contacts,
    )
    logger.info("Saving contact list to state...")
    message = [entity.json() for entity in filtered_contact_list.values()]
    config["metadata"]["last_tool"] = "get_contact"
    return str(message)


@tool
async def get_account(config: RunnableConfig):
    "Call to get list of user account"
    config_data = config.get(CONFIGURABLE_CONTEXT_KEY, {})
    ctx: RequestContext = config_data[CONTEXT_KEY]
    logger = ctx.logger()
    logger.debug("Retrieving contact list...")
    api_config = extract_bb_retail_api_config(config_data)
    accounts = await list_accounts(ctx, api_config)
    config["metadata"]["last_tool"] = "get_account"
    return str(accounts)


# @tool
# async def choice_one_contact(filtered_contacts: str, config: RunnableConfig):
#     pass


# @tool
# async def choice_one_account():
#     pass

# async def user_choice_node(state, config):
#     pass

tool_node = ToolNode([get_contact, get_account])


# %% [markdown]
#

# %%
model = (
    get_config(thread_id=THREAD_ID, cookie=cookie, access_token=access_token)
    .get(CONFIGURABLE_CONTEXT_KEY)
    .get(LLM_MODEL_KEY)
)
model

# %%
response = model.invoke(input="How the weather today")

response

# %% [markdown]
#
# ## Test workflow

# %%
import json
from app.entity.term_deposit import ActiveAccount
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import ToolMessage


def should_call_HIL(state, config):
    contacts = state.get(TransferAgentStateFields.CONTACT_LIST)
    accounts = state.get(TransferAgentStateFields.ACCOUNT_LIST)

    if len(contacts) == 1 and len(accounts) == 1:
        return "review"
    if len(contacts) > 1:
        return "select_contact"
    if len(accounts) > 1:
        return "select_account"
    return "end"


def should_continue(state, config):
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return should_call_HIL(state, config)
    else:
        return "call_tool"


tools = [get_contact, get_account]
system_prompt = """
You are a helpful AI assistant helping user to interact with transfer money flow.
Use the provided tools to progess transfer flow step by step:
    1. Extract reciepient and amount of money from user query
    2. Get list of contacts using extracted recipient name, if there are muliple recipient, ask user to choose one otherwise, process next step. If there is no contact, ask user to choose another one.
    3. Get list of user Account, if there are multiple account, ask user to chose one. If all account are insufficient, ask user for checking account balance and try again later.
    4. Review all choosen info.
You have access to the following tolls: {tool_names}.
"""
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ]
)
prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))


async def call_model(state, config):
    messages = state["messages"]
    output = {}
    if isinstance(messages[-1], ToolMessage):
        if messages[-1].name == "get_contact":
            contacts = eval(messages[-1].content)
            output["contacts"] = [
                Contact(**json.loads(contact)) for contact in contacts
            ]
        elif messages[-1].name == "get_account":
            accounts = eval(messages[-1].content)
            output["accounts"] = [
                ActiveAccount(**json.loads(account)) for account in accounts
            ]

    model_with_tools = prompt | model.bind_tools(tools)
    response = await model_with_tools.ainvoke({"messages": messages})
    output["messages"] = [response]
    return output


async def human_choice(state, config):
    pass


async def review(state, config):
    return {"messages": AIMessage(content="Let's review")}


tool_node = ToolNode(tools)


# %%
from app.assistant_v2.transfer.state import TransferAgentState
from langgraph.graph import END, START, StateGraph

workflow = StateGraph(TransferAgentState)
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)
workflow.add_node("select_contact", human_choice)
workflow.add_node("select_account", human_choice)
workflow.add_node("review", review)


workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "call_tool": "action",
        "end": END,
        "select_contact": "select_contact",
        "select_account": "select_account",
        "review": "review",
    },
)
workflow.add_edge("action", "agent")
workflow.add_edge("select_contact", "agent")
workflow.add_edge("select_account", "agent")
workflow.add_edge("review", END)
app = workflow.compile()


# %%

from IPython.display import Image, display

try:
    display(Image(app.get_graph(xray=True).draw_mermaid_png()))
except Exception:
    # This requires some extra dependencies and is optional
    pass

# %%
inputs = {"messages": [HumanMessage(content="Transfer $500 to David")]}

async for output in app.astream(inputs, config=config, stream_mode="values"):
    for key, value in output.items():
        print(f"KEY: {key}")
        print("-------------")
        print(value)
    print(">>>>>>>>>>>")

# %%
r = await get_contact("David", config, {})
r

# %%
import json

[json.loads(v) for v in r]

# %% [markdown]
# ## Workflow from code

# %%
from app.assistant_v2.transfer.graph.transfer_graph import TransferGraph

# %%
from IPython.display import Image, display

display(Image((await TransferGraph().get_graph()).draw_mermaid_png()))

# %%
from langfuse.utils.langfuse_singleton import LangfuseSingleton

lf = LangfuseSingleton().get()

# %%
from app.core.config import settings

tmpl = lf.get_prompt(
    name=settings.transfer_v2_extract_info_prompt,
    label=settings.transfer_v2_extract_info_prompt_label,
    type="chat",
)
tmpl.compile()

# %%
tmpl.get_langchain_prompt()

# %%
ChatPromptTemplate.from_messages(tmpl.get_langchain_prompt())

# %%
