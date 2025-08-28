from dataclasses import dataclass
from typing import Optional

from langchain_openai import AzureChatOpenAI

from app.core import RequestContext
from app.prompt.prompt_service import PromptService


@dataclass
class BaseAgentConfigEntity:
    thread_id: Optional[str]

    ctx: RequestContext
    llm_model: AzureChatOpenAI
    prompt_service: PromptService
