from typing import Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langfuse.model import ChatMessageDict

from app.core.config import settings
from app.llm.llm_wrapper import AzureChatOpenAIWrapper


class ChatPrompt:
    def __init__(
        self,
        name: str,
        chat_messages: list[ChatMessageDict],
        tmpl: ChatPromptTemplate,
        config: Optional[dict[str, Any]] = None,
    ):
        self.name = name
        self.chat_messages = chat_messages
        self.tmpl = tmpl
        self.configs = config or {}

    @property
    def llm_model(self) -> AzureChatOpenAIWrapper:
        config = self.configs or {}
        if "azure_deployment" not in config:
            config["azure_deployment"] = settings.azure_openai_deployment
        if "temperature" not in config:
            config["temperature"] = settings.llm_temperature
        if "api_version" not in config:
            config["api_version"] = settings.openai_api_version
        return AzureChatOpenAIWrapper(**config)
