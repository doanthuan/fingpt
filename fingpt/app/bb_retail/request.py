import json
from typing import Any, Optional, Union

import aiofiles
from aiohttp import ClientResponse, ClientSession

from app.bb_retail.api_parser_factory import ApiParserFactory
from app.bb_retail.url_provider_factory import UrlProviderFactory
from app.core.context import RequestContext
from app.entity import BbHeader, BbQueryPaging, BbQueryParams, UnauthorizedError
from app.entity.bb_api import BbApiConfig, BBRuntime
from app.entity.card import Card  # type: ignore
from app.entity.error import EbpInternalError
from app.entity.term_deposit import (
    ActiveAccount,
    TermDepositAccount,
    TermDepositProduct,
    TermUnit,
)
from app.entity.transaction import Transaction
from app.entity.transfer import Contact
from app.utils.modified_langfuse_decorator import observe  # type: ignore


class BbApiRequest:
    def __init__(self, runtime: Optional[BBRuntime] = None):
        self.url_provider = UrlProviderFactory.get_url_provider(runtime)
        self.api_parser = ApiParserFactory.get_api_parser()

    def _build_header(self, config: BbApiConfig) -> BbHeader:
        if "Bearer " not in config.ebp_access_token:
            return BbHeader(
                authorization=f"Bearer {config.ebp_access_token}",
                cookie=str(config.ebp_cookie),
            )

        return BbHeader(
            authorization=config.ebp_access_token,
            cookie=str(config.ebp_cookie),
        )

    @observe()
    async def get_balance(
        self,
        ctx: RequestContext,
        config: BbApiConfig,
    ) -> float:
        logger = ctx.logger()
        logger.debug("Getting account balance...")
        url = self.url_provider.product_summary_url().format(
            edge_domain=config.ebp_edge_domain
        )
        header = self._build_header(config)
        resp = await self._make_request(ctx, url, header)
        products = resp["currentAccounts"]["products"]
        if not products:
            return 0.0
        return min(
            [float(p["availableBalance"]) for p in products if p["availableBalance"]]
        )

    @observe()
    async def list_contacts(
        self,
        ctx: RequestContext,
        config: BbApiConfig,
        params: BbQueryPaging,
    ) -> list[Contact]:
        logger = ctx.logger()
        logger.debug("Getting contact list...")
        url = self.url_provider.contact_list_url().format(
            edge_domain=config.ebp_edge_domain
        )
        header = self._build_header(config)
        contacts = await self._make_request(ctx, url, header, params)
        return self.api_parser.parse_contacts(contacts)

    @observe()
    async def filter_transactions(
        self,
        ctx: RequestContext,
        config: BbApiConfig,
        params: Optional[BbQueryParams] = BbQueryParams(query=""),
    ) -> list[Transaction]:
        logger = ctx.logger()
        logger.debug("Getting transaction history...")
        transaction_url = self.url_provider.transaction_url().format(
            edge_domain=config.ebp_edge_domain
        )
        header = self._build_header(config)
        transaction_response = await self._make_request(
            ctx, transaction_url, header, params
        )

        parsed_transaction = self.api_parser.parse_transactions(
            transaction_response, params.query
        )
        logger.debug(f"Got transaction history: {parsed_transaction}")

        logger.debug("Getting payment history...")

        payment_url = self.url_provider.payment_url().format(
            edge_domain=config.ebp_edge_domain
        )
        params.orderBy = "requestedExecutionDate"
        payment_response = await self._make_request(ctx, payment_url, header, params)
        parsed_payment = self.api_parser.parse_payment(payment_response)
        logger.debug(f"Got payment history: {parsed_payment}")

        transaction_list = [*parsed_transaction, *parsed_payment]

        return transaction_list

    @observe()
    async def filter_transactions_v1(
        self,
        ctx: RequestContext,
        url: str,
        header: BbHeader,
        params: Optional[BbQueryParams] = BbQueryParams(query=""),
    ) -> list[Any]:
        logger = ctx.logger()
        logger.debug("Getting transaction history...")
        return await self._make_request(ctx, url, header, params)

    @observe()
    async def list_accounts(
        self,
        ctx: RequestContext,
        config: BbApiConfig,
    ) -> list[ActiveAccount]:
        logger = ctx.logger()
        logger.debug("Getting list accounts...")
        url = self.url_provider.product_summary_url().format(
            edge_domain=config.ebp_edge_domain
        )
        header = self._build_header(config)
        resp = await self._make_request(ctx, url, header)

        current_accounts = resp.get("currentAccounts", {"products": []}).get(
            "products", []
        )
        savings_accounts = resp.get("savingsAccounts", {"products": []}).get(
            "products", []
        )
        if current_accounts + savings_accounts:
            return self.api_parser.parse_accounts(current_accounts + savings_accounts)
        else:
            return self.api_parser.parse_accounts(resp)

    @observe()
    async def list_cards(
        self,
        ctx: RequestContext,
        config: BbApiConfig,
    ) -> list[Card]:
        logger = ctx.logger()
        logger.debug("Getting list cards...")
        token = config.ebp_access_token
        url = self.url_provider.card_list_url(token=token).format(
            edge_domain=config.ebp_edge_domain
        )
        header = self._build_header(config)
        cards = await self._make_request(ctx, url, header)

        return self.api_parser.parse_cards(cards)

    @observe()
    async def _make_request(
        self,
        ctx: RequestContext,
        url: str,
        header: BbHeader,
        params: Optional[Union[BbQueryParams, BbQueryPaging]] = None,
    ):
        logger = ctx.logger()
        logger.debug(f"Making request to {url}...")
        logger.debug(f"Params: {params.model_dump() if params else None}")
        async with ClientSession() as session:
            async with session.get(
                url=url,
                headers=header.model_dump(),
                params=params.model_dump() if params else None,
            ) as resp:
                await self._handle_response_errors(resp, url)
                return await resp.json()

    @staticmethod
    async def _handle_response_errors(resp: ClientResponse, url: str) -> None:
        """
        Handle errors based on the response status.

        Args:
            resp: The HTTP response object.
            url: The URL that was requested.

        Raises:
            UnauthorizedError: If the response status is 401.
            Exception: For any other non-200 response status.
        """
        if resp.status == 401:
            raise UnauthorizedError("Invalid credentials data!")
        if resp.status == 500:
            raise EbpInternalError("Something is wrong with EBP!")
        if resp.status != 200:
            raise Exception(f"Error executing GET request on {url}: {resp}")

    @observe()
    async def list_td_products(self, ctx: RequestContext) -> list[TermDepositProduct]:
        logger = ctx.logger()
        logger.debug("Getting available term deposit product list...")

        async with aiofiles.open(
            "./app/bb_retail/mock_data/term_deposits.json", "r"
        ) as file:
            file_contents = await file.read()

        products = json.loads(file_contents)

        return [
            TermDepositProduct(
                id=product.get("id"),
                name=product.get("displayName"),
                interest_rate=product.get("accountInterestRate"),
                term_number=product.get("termNumber"),
                term_unit=TermUnit(product.get("termUnit")),
                minimum_required_balance=product.get("minimumRequiredBalance"),
                maturity_earn=product.get("maturityEarn", 0),
                is_available=product.get("isAvailable", False),
            )
            for product in products
        ]

    @observe()
    async def list_term_deposit_accounts(
        self, ctx: RequestContext, config: BbApiConfig
    ) -> list[TermDepositAccount]:
        logger = ctx.logger()
        logger.debug("Getting list term deposit accounts...")

        url = self.url_provider.product_summary_url().format(
            edge_domain=config.ebp_edge_domain
        )
        resp = await self._make_request(ctx, url, self._build_header(config))
        if "currentAccounts" not in resp:
            account_holder_name = resp[0]["accountHolderNames"].lower()
        else:
            account_holder_name = resp["currentAccounts"]["products"][0][
                "accountHolderNames"
            ].lower()
        logger.debug(f"Account holder name: {account_holder_name}")

        file_paths = {
            "sara": "./app/bb_retail/mock_data/sara_account_info.json",
            "henry": "./app/bb_retail/mock_data/henry_account_info.json",
        }

        file_path = next(
            (path for name, path in file_paths.items() if name in account_holder_name),
            None,
        )

        if file_path:
            async with aiofiles.open(file_path, "r") as file:
                account_info = await file.read()
                term_deposit_accounts = (
                    json.loads(account_info).get("termDeposits", {}).get("products", [])
                )
        else:
            term_deposit_accounts: list[Any] = []

        logger.debug(f"Term deposit accounts: {term_deposit_accounts}")
        return [
            TermDepositAccount(
                id=account.get("id"),
                name=account.get("name"),
                interest_rate=account.get("interestRate"),
                term_number=account.get("termNumber"),
                term_unit=(
                    TermUnit(account.get("termUnit"))
                    if account.get("termUnit")
                    else None
                ),
                maturity_date=account.get("maturityDate"),
                bban=account.get("bban"),
                deposit_amount=account.get("bookedBalance"),
                start_date=account.get("startDate", ""),
                maturity_earn=account.get("maturityEarn", 0),
                is_mature=account.get("isMature", False),
                is_renewable=account.get("isRenewable", False),
            )
            for account in term_deposit_accounts
        ]


bbrequest = BbApiRequest()
list_term_deposit_accounts = bbrequest.list_term_deposit_accounts
list_accounts = bbrequest.list_accounts
list_contacts = bbrequest.list_contacts
list_cards = bbrequest.list_cards
filter_transactions = bbrequest.filter_transactions
filter_transactions_v1 = bbrequest.filter_transactions_v1
get_balance = bbrequest.get_balance
list_td_products = bbrequest.list_td_products
