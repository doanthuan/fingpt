from dependency_injector import containers, providers

from .fin_service import FinService
from .sec_service import SecService


class FinanceModule(containers.DeclarativeContainer):
    fin_srv: providers.Provider[FinService] = providers.Singleton(FinService)
    sec_srv: providers.Provider[SecService] = providers.Singleton(SecService)
