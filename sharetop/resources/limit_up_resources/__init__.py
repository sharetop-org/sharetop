"""Limit up resources for ShareTop API."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..._base_client import SyncAPIClient

from .dragon_tiger_data import DragonTigerData
from .limit_up_down_pool import LimitUpDownPoolData
from .market_situation import MarketSituationData
from .sector_quotes_data import SectorQuotesData


class LimitUpResources:
    """Limit up resources container.

    Provides access to limit up related data endpoints.

    Examples
    --------
    >>> client = ShareTop(api_key="your-key")
    >>> # 龙虎榜明细
    >>> df = client.limit_up.dragon_tiger_data.dragon_tiger_individual(period="近一年", as_df=True)
    >>> # 龙虎榜机构买卖每日统计
    >>> df = client.limit_up.dragon_tiger_data.dragon_institution_daily(as_df=True)
    >>> # 板块涨停数据
    >>> df = client.limit_up.sector_quotes_data.get(field_type="1", as_df=True)
    >>> # 市场概况数据
    >>> df = client.limit_up.market_situation.get(as_df=True)
    >>> # 涨跌停池数据
    >>> df = client.limit_up.limit_up_down_pool.limit_up(as_df=True)
    """

    def __init__(self, client: "SyncAPIClient") -> None:
        self._client = client
        self._dragon_tiger_data = DragonTigerData(client)
        self._sector_quotes_data = SectorQuotesData(client)
        self._market_situation = MarketSituationData(client)
        self._limit_up_down_pool = LimitUpDownPoolData(client)

    @property
    def dragon_tiger_data(self) -> DragonTigerData:
        """Dragon Tiger data (龙虎榜数据).

        Provides access to:
        - dragon_tiger_individual: 龙虎榜明细
        - dragon_institution_daily: 龙虎榜机构买卖每日统计
        - dragon_tiger_detail: 龙虎榜详情
        """
        return self._dragon_tiger_data

    @property
    def sector_quotes_data(self) -> SectorQuotesData:
        """Sector Quotes data (板块涨停数据).

        Provides access to:
        - get: 通用获取方法
        - industry: 行业涨停板
        - concept: 概念涨停板
        - region: 地域涨停板
        """
        return self._sector_quotes_data

    @property
    def market_situation(self) -> MarketSituationData:
        """Market Situation data (市场概况数据).

        Provides access to:
        - get: 通用获取方法
        """
        return self._market_situation

    @property
    def limit_up_down_pool(self) -> LimitUpDownPoolData:
        """Limit up/down pool data (涨跌停池数据).

        Provides access to:
        - limit_down: 跌停池
        - broken_limit: 破板池
        - sub_new: 次新股池
        - strong: 强势股池
        - limit_up: 涨停池
        - yes_limit_stats: 昨日涨停统计
        """
        return self._limit_up_down_pool


__all__ = [
    "LimitUpResources",
    "DragonTigerData",
    "SectorQuotesData",
    "MarketSituationData",
    "LimitUpDownPoolData",
]