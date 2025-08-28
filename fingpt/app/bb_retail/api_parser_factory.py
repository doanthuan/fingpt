from app.bb_retail.base_api_parser import BaseApiParser
from app.bb_retail.local_api_parser import LocalApiParser


class ApiParserFactory:
    @staticmethod
    def get_api_parser() -> BaseApiParser:
        # right now, only client-api is supported
        return LocalApiParser()
