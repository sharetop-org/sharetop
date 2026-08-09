"""Sector quotes data resources for ShareTop API."""

from __future__ import annotations

from typing import Union

from ..._types import NOT_GIVEN, NotGiven
from .._base import SyncResource
from ._common import convert_to_dataframe_with_timestamp, request_data

import pandas as pd

# Endpoints
SECTOR_QUOTES_ENDPOINT = "/getData/static/getStockSectorQuotes"
REALTIME_SECTOR_QUOTES_ENDPOINT = "/getData/realtime/stockSectorQuotes"

# Default field type
DEFAULT_FIELD_TYPE = "1"

# Field type options
FIELD_TYPE_INDUSTRY = "1"  # 行业涨停板
FIELD_TYPE_CONCEPT = "2"  # 概念涨停板
FIELD_TYPE_REGION = "3"  # 地域涨停板

# Default count sort
DEFAULT_COUNT_SORT = "1"

# Count sort options
COUNT_SORT_ASC = "1"  # 升序
COUNT_SORT_DESC = "2"  # 降序


class SectorQuotesData(SyncResource):
    """Synchronous interface for Sector Quotes data (板块涨停数据).

    Examples
    --------
    >>> client = ShareTop(api_key="your-key")
    >>> df = client.limit_up.sector_quotes_data.get(field_type="1", as_df=True)
    >>> df = client.limit_up.sector_quotes_data.industry(as_df=True)
    """

    def get(
            self,
            *,
            start_date: Union[str, None, NotGiven] = NOT_GIVEN,
            end_date: Union[str, None, NotGiven] = NOT_GIVEN,
            field_type: Union[str, None, NotGiven] = NOT_GIVEN,
            fields: Union[str, None, NotGiven] = NOT_GIVEN,
            as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Get Sector Quotes data (板块涨停数据).

        Parameters
        ----------
        start_date : str, optional
            Filter: trade_date >= start_date (YYYYMMDD).
        end_date : str, optional
            Filter: trade_date <= end_date (YYYYMMDD).
        field_type : str, optional
            Field type. Options: "1"=行业涨停板, "2"=概念涨停板, "3"=地域涨停板.
            Default: "1" (行业涨停板).
        fields : str, optional
            Output fields to return, separated by commas.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.

        Returns
        -------
        list or DataFrame
            Sector quotes data.
        """
        return request_data(
            self._client,
            SECTOR_QUOTES_ENDPOINT,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            as_df=as_df,
            field_type=field_type if not isinstance(field_type, NotGiven) else DEFAULT_FIELD_TYPE,
        )

    def industry(self, **kwargs) -> Union[list, "pd.DataFrame"]:
        """Get Industry limit up data (行业涨停板)."""
        kwargs["field_type"] = FIELD_TYPE_INDUSTRY
        return self.get(**kwargs)

    def concept(self, **kwargs) -> Union[list, "pd.DataFrame"]:
        """Get Concept limit up data (概念涨停板)."""
        kwargs["field_type"] = FIELD_TYPE_CONCEPT
        return self.get(**kwargs)

    def region(self, **kwargs) -> Union[list, "pd.DataFrame"]:
        """Get Region limit up data (地域涨停板)."""
        kwargs["field_type"] = FIELD_TYPE_REGION
        return self.get(**kwargs)

    # Convenience alias
    def __call__(
            self,
            *,
            start_date: Union[str, None, NotGiven] = NOT_GIVEN,
            end_date: Union[str, None, NotGiven] = NOT_GIVEN,
            field_type: Union[str, None, NotGiven] = NOT_GIVEN,
            fields: Union[str, None, NotGiven] = NOT_GIVEN,
            as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Alias for get() method."""
        return self.get(
            start_date=start_date,
            end_date=end_date,
            field_type=field_type,
            fields=fields,
            as_df=as_df,
        )

    def realtime(
            self,
            *,
            field_type: Union[str, None, NotGiven] = NOT_GIVEN,
            count_sort: Union[str, None, NotGiven] = NOT_GIVEN,
            as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Get realtime Sector Quotes data (实时板块涨停数据).

        Parameters
        ----------
        field_type : str, optional
            Field type. Options: "1"=行业涨停板, "2"=概念涨停板, "3"=地域涨停板.
            Default: "1" (行业涨停板).
        count_sort : str, optional
            Sort by count. Options: "1"=升序, "2"=降序.
            Default: "1" (升序).
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.

        Returns
        -------
        list or DataFrame
            Realtime sector quotes data.

        Examples
        --------
        >>> client = ShareTop(api_key="your-key")
        >>> # Get realtime industry sector quotes (default)
        >>> df = client.limit_up.sector_quotes_data.realtime(as_df=True)
        >>> # Get realtime concept sector quotes, sorted by count descending
        >>> df = client.limit_up.sector_quotes_data.realtime(field_type="2", count_sort="2", as_df=True)
        >>> # Get realtime region sector quotes
        >>> df = client.limit_up.sector_quotes_data.realtime(field_type="3", as_df=True)
        """
        # Set defaults if not provided
        _field_type = DEFAULT_FIELD_TYPE if isinstance(field_type, NotGiven) or field_type is None else field_type
        _count_sort = DEFAULT_COUNT_SORT if isinstance(count_sort, NotGiven) or count_sort is None else count_sort

        # Build request payload
        payload = {
            "field_type": _field_type,
            "count_sort": _count_sort,
        }

        # Execute POST request
        response = self._client.post(
            REALTIME_SECTOR_QUOTES_ENDPOINT,
            json=payload,
        )
        respCode = response.get("respCode")
        if respCode != "0000":
            return response.get("respMsg")

        # Handle response
        results = response.get("data", {}) if isinstance(response, dict) else []
        if not results:
            return response.get("message")
        results = results.get("data_list", [])

        if as_df:
            return convert_to_dataframe_with_timestamp(results)

        return results
