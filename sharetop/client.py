"""Main client classes for ShareTop API.

This module provides the primary interfaces for interacting with the ShareTop API:
- `ShareTop`: Synchronous client
- `AsyncShareTop`: Asynchronous client

Both clients provide access to the same resources with consistent method signatures.
"""

from __future__ import annotations

from typing import Any, Optional

from ._base_client import DEFAULT_MAX_RETRIES, SyncAPIClient
from ._cache import InstrumentNameCache
from ._types import Headers, Timeout
from .resources import (
    Financials,
    Klines,
    Quotes,
    Universes,
    Macro,
)
from .resources.limit_up_resources import LimitUpResources

__all__ = ["ShareTop"]


class ShareTop:
    """Synchronous client for ShareTop market data API.

    Provides access to market data including K-lines, quotes, instruments,
    exchanges, and universes.

    Parameters
    ----------
    api_key : str, optional
        API key for authentication. If not provided, reads from SHARETOP_API_KEY
        environment variable.
    base_url : str, optional
        Base URL for the API. Defaults to https://api.sharetop.com.
        Can also be set via SHARETOP_BASE_URL environment variable.
    timeout : float, optional
        Request timeout in seconds. Defaults to 30.0.
    default_headers : dict, optional
        Default headers to include in all requests.

    Attributes
    ----------
    klines : Klines
        K-line (OHLCV) data endpoints, including adjustment factors.
        Supports DataFrame conversion and forward/backward adjustment.
    quotes : Quotes
        Real-time quote endpoints.
    instruments : Instruments
        Instrument metadata endpoints.
    exchanges : Exchanges
        Exchange list endpoints.
    universes : Universes
        Universe (symbol pool) endpoints.
    financials : Financials
        Financial statement endpoints (income, balance sheet, cash flow, metrics).
    macro : Macro
        Macroeconomic indicator endpoints (GDP, CPI, PMI, etc.).
    """

    klines: Klines
    quotes: Quotes
    # instruments: Instruments
    universes: Universes
    financials: Financials
    macro: Macro
    # realtime: QuoteStream

    def __init__(
        self,
        token: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Timeout = 30.0,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Headers] = None,
        cache_dir: Optional[str] = None,
    ) -> None:
        self._client = SyncAPIClient(
            api_key=token,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )
        self._instrument_cache = InstrumentNameCache(cache_dir=cache_dir)

        self.klines = Klines(self._client, instrument_cache=self._instrument_cache)
        self.quotes = Quotes(self._client)
        # self.instruments = Instruments(self._client)
        self.universes = Universes(self._client)
        self.financials = Financials(self._client)
        self.macro = Macro(self._client)
        # self.realtime = QuoteStream(self._client)
        # Limit up resources
        self.limit_up = LimitUpResources(self._client)

    def __enter__(self) -> "ShareTop":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client.

        This releases any network resources held by the client.
        Called automatically when using the client as a context manager.
        """
        self._client.close()

    @property
    def instrument_cache(self) -> InstrumentNameCache:
        """The shared instrument name cache."""
        return self._instrument_cache

    @property
    def api_key(self) -> Optional[str]:
        """The API key used for authentication. None for free tier."""
        return self._client.api_key

    @property
    def base_url(self) -> str:
        """The base URL for API requests."""
        return self._client.base_url
