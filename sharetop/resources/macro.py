"""Macro resources for ShareTop API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pandas import DataFrame

from .._types import NOT_GIVEN, NotGiven
from ._base import SyncResource


def _to_dataframe(data: Any, as_df: bool = False) -> Union[List, "pd.DataFrame"]:
    """Convert data to DataFrame or return as-is."""
    if as_df:
        return pd.DataFrame(data) if data else pd.DataFrame()
    return data if data else []


class Macro(SyncResource):
    """Synchronous interface for macroeconomic indicator endpoints.

    Macro endpoints expose monthly/key economic indicators, such as FDI, GDP, PMI, etc.
    """

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        as_df: bool = False,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Execute POST request and return data.

        Parameters
        ----------
        endpoint : str
            API endpoint path.
        params : dict, optional
            Request parameters (e.g., ``fields``).
        as_df : bool
            Whether to return a DataFrame.

        Returns
        -------
        list or DataFrame
            Response data.
        """
        if params is None:
            params = {}
        response = self._client.post(endpoint, json=params)
        resp_code = response.get("respCode")
        msg = response.get("respMsg")
        if resp_code != "0000":
            return msg
        return _to_dataframe(response.get("data"), as_df)

    def _build_params(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Build request parameters from keyword arguments."""
        params: Dict[str, Any] = {}

        if not isinstance(fields, NotGiven) and fields:
            params["fields"] = fields

        # Add additional kwargs
        for key, value in kwargs.items():
            if value:
                params[key] = value

        return params

    def get_fdi(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get macro FDI (Foreign Direct Investment) data.

        Parameters
        ----------
        fields : str, optional
            Output fields (e.g., ``"month,fdi_fdi"``).
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            FDI data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroFdiData", params, as_df)

    def get_gross_rate(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get macro gross rate data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            Gross rate data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroGrData", params, as_df)

    def get_gfer(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get macro GFER (Gold & Foreign Exchange Reserves) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            GFER data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroGferData", params, as_df)

    def get_csto(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get macro CSTO data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            CSTO data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroCstoData", params, as_df)

    def get_ms(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get MS (money supply) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            Money supply data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroMsData", params, as_df)

    def get_cie(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get CIE (capacity utilization) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            CIE data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroCieData", params, as_df)

    def get_cci(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get CCI (Consumer Confidence Index) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            CCI data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroCciData", params, as_df)

    def get_cgpi(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get CGPI (Corporate Goods Price Index) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            CGPI data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroCgpiData", params, as_df)

    def get_iva(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get IVA (industrial value added) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            IVA data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroIvaData", params, as_df)

    def get_pmi(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get PMI (Purchasing Managers' Index) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            PMI data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroPmiData", params, as_df)

    def get_bci(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get BCI (Business Climate Index) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            BCI data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroBciData", params, as_df)

    def get_fai(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get FAI (Fixed Asset Investment) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            FAI data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroFaiData", params, as_df)

    def get_gdp(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get GDP (Gross Domestic Product) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            GDP data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroGdpData", params, as_df)

    def get_ppi(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get PPI (Producer Price Index) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            PPI data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroPpiData", params, as_df)

    def get_cpi(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get CPI (Consumer Price Index) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            CPI data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroCpiData", params, as_df)

    def get_ntr(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get NTR (National Tax Revenue, 全国税收收入) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            National tax revenue data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroNtrData", params, as_df)

    def get_tsf(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get TSF (新增信贷, Total Social Financing credit) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            TSF credit (新增信贷) data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroTsfData", params, as_df)

    def get_lcy(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get LCY (本外币存款, Local & Foreign Currency Deposits) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            LCY (本外币存款) data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroLcyData", params, as_df)

    def get_fx_loan(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get FX loan (外汇贷款) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            FX loan (外汇贷款) data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroFxLoanData", params, as_df)

    def get_rrr(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get RRR (存款准备金率, Reserve Requirement Ratio) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            RRR (存款准备金率) data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroRrrData", params, as_df)

    def get_rate_decision(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get rate decision (利率调整) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            Rate decision (利率调整) data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroRateDecisionData", params, as_df)

    def get_sc(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get SC (中国主要成品油价格, refined oil price) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            SC (成品油价格) data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroScData", params, as_df)

    def get_lpr(
        self,
        fields: Union[str, None, NotGiven] = NOT_GIVEN,
        as_df: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Get LPR (贷款市场报价利率, Loan Prime Rate) data.

        Parameters
        ----------
        fields : str, optional
            Output fields.
        as_df : bool, optional
            If True, return a pandas DataFrame. Default: False.
        **kwargs : Any
            Additional request parameters.

        Returns
        -------
        list or DataFrame
            LPR (贷款市场报价利率) data.
        """
        params = self._build_params(fields=fields, **kwargs)
        return self._request("/getData/static/getMacroLprData", params, as_df)