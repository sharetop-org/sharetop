"""Universe resources for ShareTop API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pandas import DataFrame

from .._types import NOT_GIVEN, NotGiven
from ..utils import is_valid_yyyymmdd
from ._base import SyncResource


def _to_dataframe(data: Any, as_df: bool = False) -> Union[List, "pd.DataFrame"]:
    """Convert data to DataFrame or return as-is."""
    if as_df:
        return pd.DataFrame(data) if data else pd.DataFrame()
    return data if data else []


class Universes(SyncResource):
    """Synchronous interface for universe (symbol pool) endpoints.

    Universes are predefined collections of symbols, such as "A-shares" or "US equities".
    """

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        as_df: bool = False,
    ) -> str | list | DataFrame | Any:
        """Execute POST request and return data.

        Parameters
        ----------
        endpoint : str
            API endpoint path.
        params : dict, optional
            Request parameters.
        as_df : bool
            Whether to return DataFrame.

        Returns
        -------
        list or DataFrame
            Response data.
        """
        if params is None:
            params = {}
        response = self._client.post(endpoint, json=params)
        respCode = response.get("respCode")
        msg = response.get("respMsg")
        if respCode != "0000":
            return msg
        return _to_dataframe(response.get("data"), as_df)

    def _build_params(
        self,
        ts_code: Union[str, None, NotGiven] = NOT_GIVEN,
        name: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Build request parameters from keyword arguments."""
        params: Dict[str, Any] = {}

        if not isinstance(ts_code, NotGiven) and ts_code:
            params["ts_code"] = ts_code
        if not isinstance(name, NotGiven) and name:
            params["name"] = name
        if not isinstance(fields, NotGiven) and fields:
            params["fields"] = fields

        # Add additional kwargs
        for key, value in kwargs.items():
            if value:
                params[key] = value

        return params

    def get(
        self,
        ts_code: Union[str, None, NotGiven] = NOT_GIVEN,
        name: Union[str, None, NotGiven] = NOT_GIVEN,
        market_sign: Optional[List[str]] = None,
        list_status: str = "L",
        is_hs: str = "",
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[List[Dict[str, str]], "pd.DataFrame"]:
        """Get detailed information for a specific universe.

        Parameters
        ----------
        ts_code : str, optional
            Stock code filter.
        name : str, optional
            Name filter.
        market_sign : List[str], optional
            Market identifier (e.g., "SSE", "SZSE").
        list_status : str, optional
            Listing status: L=上市, D=退市, P=暂停上市, T=停牌. Default: L.
        is_hs : str, optional
            H=沪股通, S=深股通, N=否.
        fields : str, optional
            Output fields (e.g., "ts_code,name").
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.

        Returns
        -------
        list or DataFrame
            Universe details.
        """
        params = self._build_params(
            ts_code=ts_code,
            name=name,
            fields=fields,
            list_status=list_status if list_status else None,
            is_hs=is_hs if is_hs else None,
        )

        if market_sign:
            params["exchange"] = ",".join([s.strip() for s in market_sign])

        return self._request("/getData/static/stockInfo", params, as_df)

    def get_still_listed_st(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[List[Dict[str, str]], "pd.DataFrame"]:
        """Get list of currently listed ST stocks.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.

        Returns
        -------
        list or DataFrame
            ST stocks data.
        """
        params = self._build_params(fields=fields)
        return self._request("/getData/static/stockInfoST", params, as_df)

    def _date_request(
        self,
        endpoint: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        as_df: bool = False,
    ) -> Union[List[Dict[str, str]], "pd.DataFrame"]:
        """Execute POST request with date range parameters."""
        params: Dict[str, Any] = {}

        if start_date and is_valid_yyyymmdd(start_date):
            params["start_date"] = start_date
        if end_date and is_valid_yyyymmdd(end_date):
            params["end_date"] = end_date

        return self._request(endpoint, params, as_df)

    def get_history_and_latest_st(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        as_df: bool = False,
    ) -> Union[List[Dict[str, str]], "pd.DataFrame"]:
        """Get historical and current ST stocks (including delisted).

        Parameters
        ----------
        start_date : str, optional
            Start date (YYYYMMDD).
        end_date : str, optional
            End date (YYYYMMDD).
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.

        Returns
        -------
        list or DataFrame
            ST stocks data.
        """
        return self._date_request("/getData/static/stockInfo_ST", start_date, end_date, as_df)

    def get_trade_calendar(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        as_df: bool = False,
    ) -> Union[List[Dict[str, str]], "pd.DataFrame"]:
        """Get trade calendar for exchanges (SSE, SZSE, BSE).

        Parameters
        ----------
        start_date : str, optional
            Start date (YYYYMMDD).
        end_date : str, optional
            End date (YYYYMMDD).
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.

        Returns
        -------
        list or DataFrame
            Trade calendar data.
        """
        return self._date_request("/getData/static/getTradeCalendar", start_date, end_date, as_df)

    def get_former_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[List[Dict[str, str]], "pd.DataFrame"]:
        """Get A-share former names.

        Parameters
        ----------
        start_date : str, optional
            Announcement start date (YYYYMMDD).
        end_date : str, optional
            Announcement end date (YYYYMMDD).
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.

        Returns
        -------
        list or DataFrame
            Former names data.
        """
        params: Dict[str, Any] = {}

        if start_date and is_valid_yyyymmdd(start_date):
            params["ann_date"] = start_date
        if end_date and is_valid_yyyymmdd(end_date):
            params["ann_date"] = end_date

        if not isinstance(fields, NotGiven) and fields:
            params["fields"] = fields

        return self._request("/getData/static/getStockFormer", params, as_df)

    def get_staff_data(
        self,
        ts_code: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[List[Dict[str, str]], "pd.DataFrame"]:
        """Get company staff/executives data.

        Parameters
        ----------
        ts_code : str, optional
            Stock code.
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.

        Returns
        -------
        list or DataFrame
            Staff data.
        """
        params = self._build_params(ts_code=ts_code, fields=fields)
        return self._request("/getData/static/getStockCompareStaff", params, as_df)

    def get_company_basic_info(
        self,
        ts_code: Union[str, None, NotGiven] = NOT_GIVEN,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
    ) -> Union[List[Dict[str, str]], "pd.DataFrame"]:
        """Get company basic information.

        Parameters
        ----------
        ts_code : str, optional
            Stock code.
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.

        Returns
        -------
        list or DataFrame
            Company basic info.
        """
        params = self._build_params(ts_code=ts_code, fields=fields)
        return self._request("/getData/static/getStockCompanyInfo", params, as_df)