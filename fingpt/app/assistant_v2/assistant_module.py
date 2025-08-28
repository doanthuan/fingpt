from dependency_injector import containers, providers
from langchain_openai import AzureChatOpenAI

from app.assistant_v2.primary.controller import AssistantController
from app.assistant_v2.primary.graph import AssistantGraph
from app.core.config import settings
from app.llm.llm_wrapper import AzureChatOpenAIWrapper
from app.prompt.prompt_module import PromptModule


class AssistantModule(containers.DeclarativeContainer):
    llm: providers.Provider[AzureChatOpenAI] = providers.Factory(
        AzureChatOpenAIWrapper,
        azure_deployment=settings.azure_openai_deployment,
        temperature=settings.llm_temperature,
    )

    graph: providers.Provider[AssistantGraph] = providers.Factory(
        AssistantGraph,
        prompt_srv=PromptModule.prompt_srv,
        llm=llm,
    )

    controller: providers.Provider[AssistantController] = providers.Singleton(
        AssistantController,
        prompt_srv=PromptModule.prompt_srv,
        llm=llm,
        graph=graph,
    )
