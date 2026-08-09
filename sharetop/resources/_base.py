"""Base resource class for API resources."""

from __future__ import annotations

from typing import TypeVar

from .._base_client import SyncAPIClient


ClientT = TypeVar("ClientT", "SyncAPIClient", "AsyncAPIClient")


class SyncResource:
    """Base class for synchronous API resources."""

    _client: "SyncAPIClient"

    def __init__(self, client: "SyncAPIClient") -> None:
        self._client = client