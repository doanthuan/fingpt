from dependency_injector import containers, providers

from app.intent.intent_controller import IntentController
from app.intent.intent_service import IntentService
from app.prompt.prompt_module import PromptModule


class IntentModule(containers.DeclarativeContainer):
    intent_srv: providers.Provider[IntentService] = providers.Singleton(
        IntentService,
        prompt_srv=PromptModule.prompt_srv,
    )
    controller: providers.Provider[IntentController] = providers.Singleton(
        IntentController,
        intent_srv=intent_srv,
    )
