from dependency_injector import containers, providers

from app.prompt.prompt_service import PromptService


class PromptModule(containers.DeclarativeContainer):
    prompt_srv: providers.Provider[PromptService] = providers.Singleton(
        PromptService,
    )
