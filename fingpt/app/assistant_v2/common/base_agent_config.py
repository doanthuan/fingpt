from typing import Optional, TypedDict

from langchain_openai import AzureChatOpenAI

from app.assistant_v2.constant import (
    CONTEXT_KEY,
    EBP_ACCESS_TOKEN_KEY,
    EBP_COOKIE_KEY,
    EBP_EDGE_DOMAIN_KEY,
    LLM_MODEL_KEY,
    PROMPT_SERVICE_KEY,
    THREAD_ID_KEY,
)
from app.core import RequestContext
from app.entity.agent_config import BaseAgentConfigEntity
from app.entity.bb_api import BbApiConfig
from app.entity.chat_response import ChatRespDto
from app.prompt.prompt_service import PromptService


class BaseAgentConfig(TypedDict):
    thread_id: Optional[str]

    ctx: RequestContext
    llm_model: AzureChatOpenAI
    ps: PromptService
    pending_response: list[ChatRespDto]
    user_query: Optional[str]
    user_choice_id: Optional[str]


class BbRetailAgentConfig(BaseAgentConfig):
    ebp_access_token: Optional[str]
    ebp_cookie: Optional[str]
    ebp_edge_domain: Optional[str]


def extract_bb_retail_api_config(config_data: BbRetailAgentConfig) -> BbApiConfig:
    return BbApiConfig(
        ebp_access_token=config_data[EBP_ACCESS_TOKEN_KEY],  # type: ignore
        ebp_cookie=config_data[EBP_COOKIE_KEY],  # type: ignore
        ebp_edge_domain=config_data[EBP_EDGE_DOMAIN_KEY],  # type: ignore
    )


def extract_base_agent_config(config_data: BaseAgentConfig) -> BaseAgentConfigEntity:
    return BaseAgentConfigEntity(
        thread_id=config_data[THREAD_ID_KEY],  # type: ignore
        ctx=config_data[CONTEXT_KEY],  # type: ignore
        llm_model=config_data[LLM_MODEL_KEY],  # type: ignore
        prompt_service=config_data[PROMPT_SERVICE_KEY],  # type: ignore
    )
