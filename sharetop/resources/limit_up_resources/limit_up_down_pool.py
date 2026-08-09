"""Limit up/down pool data resources for ShareTop API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from ..._types import NOT_GIVEN, NotGiven
from .._base import SyncResource
from ._common import request_data, convert_to_dataframe_with_timestamp

import pandas as pd

# Endpoints
LIMIT_DOWN_POOL_ENDPOINT = "/getData/static/getStockLimitDownPool"
BROKEN_LIMIT_POOL_ENDPOINT = "/getData/static/getStockBrokenLimitPool"
SUB_NEW_POOL_ENDPOINT = "/getData/static/getStockSubNewPool"
STRONG_POOL_ENDPOINT = "/getData/static/getStockStrongPool"
LIMIT_UP_POOL_ENDPOINT = "/getData/static/getStockLimitUpPool"
YES_LIMIT_STATS_POOL_ENDPOINT = "/getData/static/getStockYesLimitStatsPool"

# Realtime Endpoints
REALTIME_SUB_NEW_POOL_ENDPOINT = "/getData/realtime/stockSubNewPool"
REALTIME_LIMIT_DOWN_POOL_ENDPOINT = "/getData/realtime/stockLimitDownPool"
REALTIME_STRONG_POOL_ENDPOINT = "/getData/realtime/stockStrongPool"
REALTIME_BROKEN_LIMIT_POOL_ENDPOINT = "/getData/realtime/stockBrokenLimitPool"
REALTIME_LIMIT_UP_POOL_ENDPOINT = "/getData/realtime/stockLimitUpPool"

# Realtime type options
REALTIME_TYPE_SUB_NEW = "sub_new"  # 次新股池
REALTIME_TYPE_LIMIT_DOWN = "limit_down"  # 跌停股池
REALTIME_TYPE_STRONG = "strong"  # 强势股池
REALTIME_TYPE_BROKEN_LIMIT = "broken_limit"  # 炸板股池
REALTIME_TYPE_LIMIT_UP = "limit_up"  # 涨停股池

# Endpoint mapping
REALTIME_ENDPOINT_MAP = {
    REALTIME_TYPE_SUB_NEW: REALTIME_SUB_NEW_POOL_ENDPOINT,
    REALTIME_TYPE_LIMIT_DOWN: REALTIME_LIMIT_DOWN_POOL_ENDPOINT,
    REALTIME_TYPE_STRONG: REALTIME_STRONG_POOL_ENDPOINT,
    REALTIME_TYPE_BROKEN_LIMIT: REALTIME_BROKEN_LIMIT_POOL_ENDPOINT,
    REALTIME_TYPE_LIMIT_UP: REALTIME_LIMIT_UP_POOL_ENDPOINT,
}


class LimitUpDownPoolData(SyncResource):
    """Synchronous interface for Limit up/down pool data (涨跌停池数据).

    Examples
    --------
    >>> client = ShareTop(api_key="your-key")
    >>> df = client.limit_up.limit_up_down_pool.limit_up(as_df=True)
    >>> df = client.limit_up.limit_up_down_pool.limit_down(as_df=True)
    """

    def limit_down(
        self,
        *,
        start_date: Union[str, None, NotGiven] = NOT_GIVEN,
        end_date: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Get Limit Down Pool data (跌停池)."""
        return request_data(
            self._client,
            LIMIT_DOWN_POOL_ENDPOINT,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            as_df=as_df,
        )

    def broken_limit(
        self,
        *,
        start_date: Union[str, None, NotGiven] = NOT_GIVEN,
        end_date: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Get Broken Limit Pool data (破板池)."""
        return request_data(
            self._client,
            BROKEN_LIMIT_POOL_ENDPOINT,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            as_df=as_df,
        )

    def sub_new(
        self,
        *,
        start_date: Union[str, None, NotGiven] = NOT_GIVEN,
        end_date: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Get Sub New Pool data (次新股池)."""
        return request_data(
            self._client,
            SUB_NEW_POOL_ENDPOINT,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            as_df=as_df,
        )

    def strong(
        self,
        *,
        start_date: Union[str, None, NotGiven] = NOT_GIVEN,
        end_date: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Get Strong Pool data (强势股池)."""
        return request_data(
            self._client,
            STRONG_POOL_ENDPOINT,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            as_df=as_df,
        )

    def limit_up(
        self,
        *,
        start_date: Union[str, None, NotGiven] = NOT_GIVEN,
        end_date: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Get Limit Up Pool data (涨停池)."""
        return request_data(
            self._client,
            LIMIT_UP_POOL_ENDPOINT,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            as_df=as_df,
        )

    def yes_limit_stats(
        self,
        *,
        start_date: Union[str, None, NotGiven] = NOT_GIVEN,
        end_date: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Get Yes Limit Stats Pool data (昨日涨停统计池)."""
        return request_data(
            self._client,
            YES_LIMIT_STATS_POOL_ENDPOINT,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            as_df=as_df,
        )

    def realtime(
        self,
        *,
        realtime_type: str = REALTIME_TYPE_LIMIT_UP,
        as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Get realtime pool data (实时股票池).

        Parameters
        ----------
        realtime_type : str, optional
            Pool type. Options:
            - "sub_new": 次新股池
            - "limit_down": 跌停股池
            - "strong": 强势股池
            - "broken_limit": 炸板股池
            - "limit_up": 涨停股池 (default)
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.

        Returns
        -------
        list or DataFrame
            Realtime pool data.

        Examples
        --------
        >>> client = ShareTop(api_key="your-key")
        >>> # Get realtime limit up pool (default)
        >>> data = client.limit_up.limit_up_down_pool.realtime()
        >>> df = client.limit_up.limit_up_down_pool.realtime(as_df=True)
        >>> # Get realtime sub new pool
        >>> df = client.limit_up.limit_up_down_pool.realtime(realtime_type="sub_new", as_df=True)
        >>> # Get realtime limit down pool
        >>> df = client.limit_up.limit_up_down_pool.realtime(realtime_type="limit_down", as_df=True)
        >>> # Get realtime strong pool
        >>> df = client.limit_up.limit_up_down_pool.realtime(realtime_type="strong", as_df=True)
        >>> # Get realtime broken limit pool
        >>> df = client.limit_up.limit_up_down_pool.realtime(realtime_type="broken_limit", as_df=True)
        """
        # Get endpoint based on realtime_type
        endpoint = REALTIME_ENDPOINT_MAP.get(realtime_type)
        if not endpoint:
            raise ValueError(
                f"Invalid realtime_type: {realtime_type}. "
                f"Valid options: {list(REALTIME_ENDPOINT_MAP.keys())}"
            )

        # Execute GET request
        response = self._client.get(endpoint)

        respCode = response.get("respCode")
        if respCode != "0000":
            return response.get("respMsg")

        # Handle response
        results = response.get("data", {}) if isinstance(response, dict) else []
        if isinstance(results, dict):
            results = results.get("data_list", [])

        if as_df:
            return convert_to_dataframe_with_timestamp(results)

        return results