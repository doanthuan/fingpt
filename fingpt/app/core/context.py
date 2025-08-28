from app.core.logging import Logger


class RequestContext:
    def __init__(
        self,
        req_id: str,
    ):
        self.req_id = "-".join(req_id.split(" "))
        self.base_logger = Logger(req_id)

    def logger(self) -> Logger:
        return self.base_logger

    def request_id(self) -> str:
        return self.req_id
