from typing import Optional

from ..core.config import settings
from ..entity.bb_api import BBRuntime
from .base_url_provider import BaseUrlProvider
from .istio_url_provider import IstioUrlProvider
from .local_url_provider import LocalUrlProvider


class UrlProviderFactory:
    @staticmethod
    def get_url_provider(
        env_type: Optional[BBRuntime] = None,
    ) -> BaseUrlProvider:
        if env_type is None:
            env_type = BBRuntime(settings.runtime)
        if env_type == BBRuntime.LOCAL:
            return LocalUrlProvider()
        elif env_type in [BBRuntime.EXP, BBRuntime.STAGING]:
            return IstioUrlProvider()

        raise ValueError("Invalid environment type")
