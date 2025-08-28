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
#     name: python3
# ---

# %% [markdown]
# # Ticker Agent

# %%
from app.assistant.assistant_module import AssistantModule
from app.assistant.ticker.agent import TickerAgent
from app.assistant.ticker.state import TickerAgentConfig, TickerAgentState
from langgraph.graph import END, StateGraph, START

module = AssistantModule()
agent_srv: TickerAgent = module.ticker_agent()
workflow = StateGraph(
    state_schema=TickerAgentState,
    config_schema=TickerAgentConfig,
)

agent = agent_srv._get_workflow(workflow)

from IPython.display import Image, display

# Setting xray to 1 will show the internal structure of the nested graph
display(Image(agent.get_graph(xray=1).draw_mermaid_png()))

# %% [markdown]
# # Transaction Agent

# %%
from IPython.display import Image, display

from app.assistant.transaction.agent import TransactionAgent
from app.prompt.prompt_service import PromptService

ps = PromptService()
display(Image(TransactionAgent(ps).get_display_graph()))

# %% [markdown]
# # Money Transfer Agent

# %%
from IPython.display import Image, display

from app.assistant.transfer.agent import TransferAgent
from app.prompt.prompt_service import PromptService

ps = PromptService()
display(Image(TransferAgent(ps).get_display_graph()))

# %% [markdown]
# # RENEW CARD AGENT

# %%
from IPython.display import Image, display

from app.assistant.card.agent import CardAgent
from app.prompt.prompt_service import PromptService

ps = PromptService()
display(Image(CardAgent(ps).get_display_graph()))
# %% [markdown]
# ## Term Deposit Agent

# %% [markdown]
# #### Original

# %%
from IPython.display import Image, display
from app.assistant.term_deposit.common.agent import TermDepositAgent
from app.core.context import RequestContext
from app.prompt.prompt_service import PromptService

ps = PromptService()

workflow = TermDepositAgent(ps)._get_workflow(RequestContext(""))
display(Image(workflow.compile().get_graph(xray=1).draw_mermaid_png()))

# %% [markdown]
# ### Modified

# %%
from IPython.display import Image, display
from app.assistant_v2.term_deposit.graph.term_deposit_graph import TermDepositGraph

term_deposit = TermDepositGraph()
print((await term_deposit.get_graph()).draw_mermaid())
display(Image((await term_deposit.get_graph()).draw_mermaid_png()))

# %%
