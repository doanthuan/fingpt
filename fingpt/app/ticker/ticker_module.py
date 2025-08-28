from dependency_injector import containers, providers

from app.assistant.assistant_module import AssistantModule
from app.finance.finance_module import FinanceModule
from app.prompt.prompt_module import PromptModule

from .report_service import ReportService
from .ticker_controller import TickerController


class TickerModule(containers.DeclarativeContainer):
    report_srv: providers.Provider[ReportService] = providers.Singleton(
        ReportService,
        fin_srv=FinanceModule.fin_srv,
        sec_srv=FinanceModule.sec_srv,
        prompt_srv=PromptModule.prompt_srv,
    )

    ticker_ctrl: providers.Provider[TickerController] = providers.Singleton(
        TickerController,
        report_srv=report_srv,
        ticker_agent=AssistantModule.ticker_agent,
    )
