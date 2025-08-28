from dependency_injector import containers, providers

from app.finance.finance_module import FinanceModule
from app.prompt.prompt_module import PromptModule

from .ticker.agent import TickerAgent


class AssistantModule(containers.DeclarativeContainer):
    ticker_agent: providers.Provider[TickerAgent] = providers.Singleton(
        TickerAgent,
        fin_srv=FinanceModule.fin_srv,
        sec_srv=FinanceModule.sec_srv,
        prompt_srv=PromptModule.prompt_srv,
    )
