import os
import pickle
from typing import Generic, Optional, TypeVar

import aiofiles

from app.entity.finance_service import CachedReport, StockData

T = TypeVar("T")


CACHE_DIR = ".fin-gpt-cached"

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


class CacheManager(Generic[T]):
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        self.memory: dict[str, T] = {}

    def cache_file_path(self, symbol: str, kind: str) -> str:
        file_name = f"{symbol}_{kind}.pkl"
        return os.path.join(self.cache_dir, file_name)

    async def load_cache(self, file_path: str) -> Optional[T]:
        if os.path.exists(file_path):
            async with aiofiles.open(file_path, "rb") as f:
                data = await f.read()
                return pickle.loads(data)
        return None

    async def save_cache(self, data: T, file_path: str) -> None:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(pickle.dumps(data))

    def save_memory(self, key: str, data: T) -> None:
        self.memory[key] = data

    def load_memory(self, key: str) -> Optional[T]:
        return self.memory.get(key, None)


url_cache = CacheManager[str](CACHE_DIR)
section_cache = CacheManager[str](CACHE_DIR)
report_cache = CacheManager[CachedReport](CACHE_DIR)
stock_cache = CacheManager[StockData](CACHE_DIR)
