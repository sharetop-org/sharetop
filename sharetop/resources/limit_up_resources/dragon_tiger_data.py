"""Dragon Tiger data resources for ShareTop API."""

from __future__ import annotations

from typing import Union

from ..._types import NOT_GIVEN, NotGiven
from .._base import SyncResource
from ._common import request_data

import pandas as pd

# Endpoints
TIGER_INDIVIDUAL_ENDPOINT = "/getData/static/getStockDragonTigerIndividual"
INSTITUTION_DAILY_ENDPOINT = "/getData/static/getStockDragonInstitutionDaily"
TIGER_DETAIL_ENDPOINT = "/getData/static/getStockDragonTigerDetail"

# Default period
DEFAULT_PERIOD = "近一个月"


class DragonTigerData(SyncResource):
    """Synchronous interface for Dragon Tiger data (龙虎榜数据).

    Examples
    --------
    >>> client = ShareTop(api_key="your-key")
    >>> data = client.limit_up.dragon_tiger_data.dragon_tiger_individual()
    >>> df = client.limit_up.dragon_tiger_data.dragon_tiger_individual(as_df=True)
    """

    def dragon_tiger_individual(
        self,
        *,
        start_date: Union[str, None, NotGiven] = NOT_GIVEN,
        end_date: Union[str, None, NotGiven] = NOT_GIVEN,
        period: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Get Dragon Tiger Individual data (龙虎榜明细).

        Parameters
        ----------
        start_date : str, optional
            Filter: latest_date >= start_date (YYYYMMDD).
        end_date : str, optional
            Filter: latest_date <= end_date (YYYYMMDD).
        period : str, optional
            Time period. Options: "近一个月", "近三个月", "近六个月", "近一年".
            Default: "近一个月".
        fields : str, optional
            Output fields to return, separated by commas.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.

        Returns
        -------
        list or DataFrame
            Dragon Tiger Individual data.
        """
        return request_data(
            self._client,
            TIGER_INDIVIDUAL_ENDPOINT,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            as_df=as_df,
            period=period if not isinstance(period, NotGiven) else DEFAULT_PERIOD,
        )

    def dragon_institution_daily(
        self,
        *,
        start_date: Union[str, None, NotGiven] = NOT_GIVEN,
        end_date: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Get Dragon institution daily data (龙虎榜机构买卖每日统计).

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
            Dragon institution daily data.
        """
        return request_data(
            self._client,
            INSTITUTION_DAILY_ENDPOINT,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            as_df=as_df,
        )

    def dragon_tiger_detail(
        self,
        *,
        start_date: Union[str, None, NotGiven] = NOT_GIVEN,
        end_date: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Get Dragon Tiger Detail data (龙虎榜详情).

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
            Dragon Tiger Detail data.
        """
        return request_data(
            self._client,
            TIGER_DETAIL_ENDPOINT,
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
        period: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[list, "pd.DataFrame"]:
        """Alias for dragon_tiger_individual() method."""
        return self.dragon_tiger_individual(
            start_date=start_date,
            end_date=end_date,
            period=period,
            fields=fields,
            as_df=as_df,
        )