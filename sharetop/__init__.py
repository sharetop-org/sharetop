"""ShareTop Python SDK - 高性能行情数据客户端。

支持 A股的基础数据和行情数据查询，提供同步和异步两种接口。

"""

from .__version__ import __version__
from ._exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    ConnectionError,
    InternalServerError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    ShareTopError,
    TimeoutError,
)
from .client import ShareTop


__all__ = [
    "__version__",
    # Main clients
    "ShareTop",
    # Exceptions
    "ShareTopError",
    "APIError",
    "AuthenticationError",
    "PermissionError",
    "NotFoundError",
    "BadRequestError",
    "RateLimitError",
    "InternalServerError",
    "ConnectionError",
    "TimeoutError",
]
