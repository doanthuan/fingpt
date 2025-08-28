import asyncio
from typing import Optional

from aiohttp import ClientSession
from sec_api import ExtractorApi  # type: ignore
from tenacity import retry, stop_after_attempt, stop_after_delay, wait_random

from app.core.config import settings
from app.core.context import RequestContext
from app.utils.cache_manager import section_cache, url_cache

BASE_URL = "https://api.sec-api.io"
ALLOWED_SEC_API_CALLS = settings.allowed_sec_api_calls
SEC_EDGAR_SECTIONS = list(str(i) for i in range(1, 16)) + ["1A", "1B", "7A", "9A", "9B"]


class SecService:
    def __init__(
        self,
    ) -> None:
        # self._api_key = SEC_API_KEY
        # self._extractor = ExtractorApi(SEC_API_KEY)
        self._url_cache = url_cache
        self._section_cache = section_cache

    @retry(
        reraise=True,
        stop=(stop_after_delay(60) | stop_after_attempt(3)),
        wait=wait_random(min=1, max=5),
    )
    async def get_10k_filing(
        self,
        ctx: RequestContext,
        symbol: str,
        api_key: str,
    ) -> str:
        logger = ctx.logger()
        url: Optional[str] = await self._url_cache.load_cache(
            self._url_cache.cache_file_path(symbol, "url"),
        )

        if url:
            logger.info(f"Returning cached URL {url}...")
            return url

        if ALLOWED_SEC_API_CALLS != "true":
            raise Exception("SEC API calls are disabled. Set to 'true' in .env")

        endpoint = f"{BASE_URL}?token={api_key}"

        query = {
            "query": {
                "query_string": {"query": f'ticker:{symbol} AND formType:"10-K"'}
            },
            "from": "0",
            "size": "1",
            "sort": [{"filedAt": {"order": "desc"}}],
        }

        logger.debug(f"Fetching 10-K filing for {symbol}...")
        async with ClientSession() as session:
            async with session.post(endpoint, json=query) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(
                        f"Failed to get 10-K filing for {symbol}. Response: {text}"
                    )

                filings = (await resp.json()).get("filings", [])
                if not filings:
                    raise Exception(f"No 10-K filings found for {symbol}")

                logger.info("Saving URL to cache and return...")
                await self._url_cache.save_cache(
                    filings[0]["linkToFilingDetails"],
                    self._url_cache.cache_file_path(symbol, "url"),
                )
                return filings[0]["linkToFilingDetails"]

    async def get_section(
        self,
        ctx: RequestContext,
        symbol: str,
        section: str,
        format: str,
        api_key: str,
    ) -> str:
        """
        Get 10-K reports from SEC EDGAR
        """
        logger = ctx.logger()

        if section not in SEC_EDGAR_SECTIONS:
            raise ValueError(f"Section must be in {SEC_EDGAR_SECTIONS}")

        url = await self.get_10k_filing(ctx, symbol, api_key)
        cache_file = self._section_cache.cache_file_path(symbol, section)
        cached_data: Optional[str] = await self._section_cache.load_cache(cache_file)
        if cached_data is not None:
            logger.info("Returning cached section...")
            try:
                return cached_data.decode("utf-8")
            except AttributeError:
                return cached_data

        if ALLOWED_SEC_API_CALLS != "true":
            raise Exception("SEC API calls are disabled. Set to 'true' in .env")

        extractor = ExtractorApi(api_key)
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(
            None,
            extractor.get_section,
            url,
            section,
            format,
        )
        logger.info("Saving section to cache and return...")
        try:
            decoded_data = data.decode("utf-8")
        except AttributeError:
            decoded_data = data
        await self._section_cache.save_cache(decoded_data, cache_file)
        return decoded_data
