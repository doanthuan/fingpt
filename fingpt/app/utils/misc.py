import json
import subprocess
import uuid
from typing import Any, Type, TypeVar

import yaml
from fastapi import Request
from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.entity import ChatRespAction, ChatRespDto

T = TypeVar("T")


def short_commit_SHA() -> str:
    """Retrieve the current Git commit SHA."""
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    return sha[:7]


def read_yaml(clazz: Type[T], file_path: str) -> T:
    with open(file_path, "r") as f:
        _config = yaml.safe_load(f)
    return clazz(**_config)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Any,
    ):
        print(f"Request: {request.method} {request.url}")
        headers = dict(request.headers)
        if "x-request-id" not in headers:
            new_header = MutableHeaders(request._headers)
            new_header["x-request-id"] = str(uuid.uuid4())
            request._headers = new_header
            request.scope.update(headers=request.headers.raw)

        body = await request.body()
        if body:
            try:
                print(f"Body: {body.decode('utf-8')}")
            except Exception as e:
                print(f"Error decoding body: {e}")

        return await call_next(request)


class ResponseSortingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Any,
    ):
        response = await call_next(request)
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        try:
            decoded_body = response_body.decode("utf-8")
            response_json = json.loads(decoded_body)
            reverted_response = ChatRespDto(**response_json)
            if reverted_response.action == ChatRespAction.SHOW_CHOICES:
                # Filter out disabled choices instead of sorting
                reverted_response.metadata.choices = [
                    choice
                    for choice in reverted_response.metadata.choices
                    if choice.is_enabled
                ]
                response_json = reverted_response.model_dump()
            modified_response = json.dumps(response_json).encode("utf-8")
            response.headers["Content-Length"] = str(len(modified_response))
            return Response(
                content=modified_response,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        except Exception as _:  # noqa: F841
            response.headers["Content-Length"] = str(len(response_body))
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
