"""Market situation data resources for ShareTop API."""

from __future__ import annotations

from typing import Union

from ..._types import NOT_GIVEN, NotGiven
from .._base import SyncResource
from ._common import convert_to_dataframe_with_timestamp, request_data

import pandas as pd

# Endpoints
MARKET_SITUATION_ENDPOINT = "/getData/static/getStockMarketSituation"
REALTIME_MARKET_SITUATION_ENDPOINT = "/getData/realtime/stockMarketSituation"


class MarketSituationData(SyncResource):
    """Synchronous interface for Market Situation data (市场概况数据).

    Examples
    --------
    >>> client = ShareTop(token="")
    >>> df = client.limit_up.market_situation.get(as_df=True)
    """
 
    def get(
        self,
        *,
        start_date: Union[str, None, NotGiven] = NOT_GIVEN,
        end_date: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Get Market Situation data (市场概况数据).

        Parameters
        ----------
        start_date : str, optional
            Filter: trade_date >= start_date (YYYYMMDD).
        end_date : str, optional
            Filter: trade_date <= end_date (YYYYMMDD).
        fields : str, optional
            Output fields to return, separated by commas.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.

        Returns
        -------
        list or DataFrame
            Market situation data.
        """
        return request_data(
            self._client,
            MARKET_SITUATION_ENDPOINT,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            as_df=as_df,
        )

    # Convenience alias
    def __call__(
        self,
        *,
        start_date: Union[str, None, NotGiven] = NOT_GIVEN,
        end_date: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Alias for get() method."""
        return self.get(
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            as_df=as_df,
        )

    def realtime(
        self,
        *,
        as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Get realtime Market Situation data (实时市场概况数据).

        Returns
        -------
        list or DataFrame
            Realtime market situation data.

        Examples
        --------
        >>> client = ShareTop(api_key="your-key")
        >>> data = client.limit_up.market_situation.realtime()
        >>> df = client.limit_up.market_situation.realtime(as_df=True)
        """
        # Use the public GET method from the client
        response = self._client.get(REALTIME_MARKET_SITUATION_ENDPOINT)

        respCode = response.get("respCode")
        if respCode != "0000":
            return response.get("respMsg")

        results = response.get("data", {}) if isinstance(response, dict) else []
        if not results:
            return response.get("message")
        results = results.get("data_list", [])

        if as_df:
            return convert_to_dataframe_with_timestamp(results)

        return results