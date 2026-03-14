"""
BaseCollector — shared interface for all data collectors.
Every collector must implement collect() and summary().
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
import json
import hashlib
import diskcache
import logging

logger = logging.getLogger(__name__)

CACHE_DIR = Path("data/raw")
CACHE_TTL = 60 * 60 * 6  # 6 hours in seconds


class BaseCollector(ABC):
    """
    Abstract base for all OSINT data collectors.

    Provides:
    - Shared async collect() interface
    - Disk-based caching to avoid hammering public APIs
    - Standardized error handling
    - Demo mode support for testing without API keys
    """

    name: str = "BaseCollector"
    source_key: str = "base"

    def __init__(self, region: dict, start_date: datetime, end_date: datetime, demo_mode: bool = False):
        self.region = region
        self.start_date = start_date
        self.end_date = end_date
        self.demo_mode = demo_mode
        self._result = None

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._cache = diskcache.Cache(str(CACHE_DIR))

    def _cache_key(self) -> str:
        """Generate a deterministic cache key from region + date range."""
        raw = f"{self.source_key}_{self.region['name']}_{self.start_date.date()}_{self.end_date.date()}"
        return hashlib.md5(raw.encode()).hexdigest()

    async def collect(self) -> dict:
        """
        Collect data, using disk cache when available.
        Falls back to live fetch on cache miss or expiry.
        """
        key = self._cache_key()

        cached = self._cache.get(key)
        if cached is not None:
            logger.debug(f"[{self.name}] Cache hit — {key[:8]}")
            self._result = cached
            return cached

        logger.debug(f"[{self.name}] Cache miss — fetching live data")
        data = await self._fetch()
        self._cache.set(key, data, expire=CACHE_TTL)
        self._result = data
        return data

    @abstractmethod
    async def _fetch(self) -> dict:
        """Fetch fresh data from the source. Implement in subclass."""
        pass

    @abstractmethod
    def summary(self) -> str:
        """Return a one-line human-readable summary of collected data."""
        pass
