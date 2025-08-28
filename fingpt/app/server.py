import logging
import os
import socket

import sentry_sdk
import yfinance as yf  # type: ignore
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from langchain.globals import set_llm_cache
from langchain_community.cache import InMemoryCache
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from urllib3.connection import HTTPConnection

from app.container import ServerContainer
from app.core.config import settings
from app.routers.assistant_chat import assistant_chat_router
from app.routers.backbase_auth import backbase_auth_router
from app.routers.command import command_router
from app.routers.intent import intent_router
from app.routers.profile import profile_router
from app.routers.raw_data_report import raw_data_router
from app.routers.suggestion import suggestion_router
from app.utils import RequestLoggingMiddleware
from app.utils.misc import ResponseSortingMiddleware

container = ServerContainer()

if settings.enable_semantic_cache:
    set_llm_cache(container.semantic_cache())
else:
    set_llm_cache(InMemoryCache())

# @SONAR_STOP@
tmp_dir = "/tmp"
yf.set_tz_cache_location(tmp_dir)
# @SONAR_START@


# Define the filter
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.args and len(record.args) >= 3 and record.args[2] != "/health"  # type: ignore


# Add filter to the logger
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())


# Following this instruction: https://github.com/psf/requests/issues/4937#issuecomment-788899804
HTTPConnection.default_socket_options = HTTPConnection.default_socket_options + [
    (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
    # (socket.SOL_TCP, socket.TCP_KEEPIDLE, 45),
    (socket.SOL_TCP, socket.TCP_KEEPINTVL, 10),
    (socket.SOL_TCP, socket.TCP_KEEPCNT, 6),
]

if (
    settings.sentry_dsn is not None
    and settings.sentry_dsn != ""
    and settings.runtime != "local"
):
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        environment=settings.runtime,
        release=settings.app_version,
        # same as above
        integrations=[
            StarletteIntegration(
                transaction_style="endpoint",
                failed_request_status_codes=[range(400, 599)],
            ),
            FastApiIntegration(
                transaction_style="endpoint",
                failed_request_status_codes=[range(400, 599)],
            ),
        ],
    )

app = FastAPI(
    root_path=settings.root_path,
    version=settings.app_version,
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ResponseSortingMiddleware)

# Initialize the dependency container

app.include_router(backbase_auth_router)
app.include_router(assistant_chat_router)
app.include_router(raw_data_router)
app.include_router(command_router)
app.include_router(profile_router)
app.include_router(intent_router)
app.include_router(suggestion_router)


@app.get(
    "/v1/version",
    summary="Show current version",
    response_description="Service version",
)
async def version():
    return {"version": app.version}


@app.get(
    "/health",
    summary="Health Check",
    response_description="Service health status",
)
def health_check() -> dict[str, str]:
    """
    Health check endpoint to verify the service is running.

    Args:
    - None

    Returns:
    - JSON response containing the health status of the service
    """
    return {"status": "healthy"}


app.mount(  # type: ignore
    f"/{settings.assets_url_prefix}",
    StaticFiles(directory=os.getenv("IMAGE_SAVE_PATH")),
    name="assets",
)

if __name__ == "__main__":
    import uvicorn

    port = int(settings.port)
    uvicorn.run(app, host="0.0.0.0", port=port)
