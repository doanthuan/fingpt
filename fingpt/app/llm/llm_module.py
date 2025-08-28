from dependency_injector import containers, providers

from app.llm.llm_service import LlmService
from app.llm.llm_wrapper import AzureChatOpenAIWrapper


class LlmModule(containers.DeclarativeContainer):
    llm_srv: providers.Provider[LlmService] = providers.Singleton(LlmService)


class LlmWrapperModule(containers.DeclarativeContainer):
    llm_wrapper: providers.Provider[AzureChatOpenAIWrapper] = providers.Singleton(
        AzureChatOpenAIWrapper
    )
