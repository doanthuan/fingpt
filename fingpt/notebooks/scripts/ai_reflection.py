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
from langchain_openai import AzureChatOpenAI
from langchain_core.runnables.config import RunnableConfig
from app.core.config import settings

from app.assistant.constant import (
    CONTEXT_KEY,
    EBP_ACCESS_TOKEN_KEY,
    EBP_COOKIE_KEY,
    EBP_EDGE_DOMAIN_KEY,
    LLM_MODEL_KEY,
    THREAD_ID_KEY,
)

from app.core.context import RequestContext


def get_config(thread_id):
    config = RunnableConfig(
        configurable={
            THREAD_ID_KEY: thread_id,
            CONTEXT_KEY: RequestContext(thread_id),
            LLM_MODEL_KEY: AzureChatOpenAI(
                azure_deployment=settings.azure_openai_deployment
            ),
        }
    )
    return config


# %%
from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY


THREAD_ID = "test_1"
model = get_config(thread_id=THREAD_ID).get(CONFIGURABLE_CONTEXT_KEY).get(LLM_MODEL_KEY)
model

# %%
from typing import Optional
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools.structured import StructuredTool


class EvaluateResultInput(BaseModel):
    is_a_good_answer: bool = Field(
        description="Whether the last answer is match with the instruction in the given context or not (True/False)"
    )
    reason: str = Field(
        description="The reason why the last answer is match with the instruction in the given context or not"
    )
    guidance_for_good_answer: Optional[str] = Field(
        description="If the last answer is not a good answer, generate this guidance for making a good answer which help to match with the instruction in the given context"
    )


async def _evaluate_result(
    is_a_good_answer: bool, reason: str, guidance_for_good_answer: Optional[str]
):
    return EvaluateResultInput(
        is_a_good_answer=is_a_good_answer,
        reason=reason,
        guidance_for_good_answer=guidance_for_good_answer,
    ).json()


evaluate_result_tool: StructuredTool = StructuredTool.from_function(
    coroutine=_evaluate_result,
    name="EvaluateResult",
    description="Call this tool to provide the evaluation result of the last answer to the system",
    args_schema=EvaluateResultInput,
    error_on_invalid_docstring=True,
)


# %%
from langchain_core.runnables.config import RunnableConfig
from langchain_core.prompts.chat import ChatPromptTemplate
from app.assistant_v2.constant import CONFIGURABLE_CONTEXT_KEY
from app.assistant_v2.transfer.state import TransferAgentState, TransferAgentStateFields


async def reflection_fnc(
    state: TransferAgentState, config: RunnableConfig
) -> dict[str, any]:
    prompt = """
    You are a expert judge in the field of AI response verification. Your task is to evaluate whether the AI response is correct or not based on the instruction prompt.
    You are provided with a original instruction prompt for the model and a conversation history. You need to evaluate the last response of the model and call tool named EvaluateResult to generate resutl.
    The result contains the following fields:
    - is_a_good_answer: Whether the last answer is match with the instruction in the given context or not (True/False)
    - reason: The reason why the last answer is match with the instruction in the given context or not
    - guidance_for_good_answer: If the last answer is not a good answer, generate a guidance for making a good answer which help to match with the instruction in the given context
    Here is the original instruction prompt: {{original_instruction_prompt}}
    Here is the conversation history: {{conversation_history}}
    """
    prev_prompt = config.get(CONFIGURABLE_CONTEXT_KEY)
    messages = state[TransferAgentStateFields.MESSAGES]

    prompt_tmpl = ChatPromptTemplate.from_messages([("system", prompt)])
    chain = prompt_tmpl | model.bind_tools([evaluate_result_tool])
    response = await chain.ainvoke(
        {"original_instruction_prompt": prev_prompt, "conversation_history": messages}
    )
    return response


# %%

# %%

# %%
