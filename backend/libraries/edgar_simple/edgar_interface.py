import requests
from libraries.edgar_simple.edgar_utils import *
import pandas as pd
from typing import List
from libraries.edgar_simple.edgar import EdgarData
from libraries.edgar_simple.edgar_utils import *
from libraries.edgar_simple.edgar_redirect import RedirectUtils as RU
import numpy as np
from datetime import datetime
from typing import List


class Edgar:

    def __init__(
        self,
        ticker: str,
        up_till_date_ago: datetime,
        forms: List[str] = ["8-K", "10-K", "10-Q"],
    ):
        redirected = False
        cik = EdgarData.ticker_to_cik(ticker)
        meta_data = EdgarData.get_meta_data(EdgarData.cik_serialization(cik))
        self.fiscal_month_end = datetime.strptime(
            meta_data["fiscalYearEnd"], "%m%d"
        ).month
        up_till_dates, redirect_urls = EdgarUtils.edgar_cur_to_dates(meta_data)
        new_url = EdgarUtils.redo_edgar_by_date(
            up_to_dates=up_till_dates,
            urls=redirect_urls,
            date_filter=up_till_date_ago,
        )
        if new_url:
            meta_data = RU.new_meta_data(url=new_url)
            redirected = True
        self.cik = cik
        self.meta = self.__index_by_form(meta_data, redirected, forms)

    def __index_by_form(self, meta_data, redirected, forms):
        columns_to_keep = [
            "accessionNumber",
            "filingDate",
            "reportDate",
            "form",
            "primaryDocument",
        ]
        if redirected:
            df = pd.DataFrame(meta_data)[columns_to_keep]
        else:
            df = pd.DataFrame(meta_data["filings"]["recent"])[columns_to_keep]
        return df[df["form"].isin(forms)].reset_index(drop=True)

    def parse_edgar_df(self):
        base_url = sec_config["base_filing_url"]
        self.meta["url"] = [
            f"{base_url}{self.cik}/{accessionNumb.replace('-','')}/{pdoc}"
            for accessionNumb, pdoc in zip(
                self.meta["accessionNumber"].to_list(),
                self.meta["primaryDocument"].to_list(),
            )
        ]
        # self.meta["reportDate"] = pd.to_datetime(self.meta["reportDate"])
        # self.meta["quarter"] = self.meta["reportDate"].dt.quarter
        # self.meta["year"] = self.meta["reportDate"].dt.year
        return self.meta[["filingDate", "reportDate", "form", "url"]]

    def quarter(self, dt_series):
        fiscal_quarter = dt_series.dt.month.apply(lambda x: x if x <= 12 else x + 12)
        months_from_fiscal_start = fiscal_quarter - self.fiscal_month_end
        return (months_from_fiscal_start // 3).apply(lambda x: 4 if x == 0 else x)

    def get_by(self, quarter: int = None, year: int = None, form: str = None):
        if "url" not in self.meta.columns:
            self.parse_edgar_df()
        df = self.meta[["filingDate", "reportDate", "form", "url"]].copy(deep=True)
        df["reportDate"] = pd.to_datetime(df["reportDate"])
        df["quarter"] = self.quarter(df["reportDate"])
        df = df[df["form"] == form]
        if quarter and year:
            cond_1 = df["quarter"] == quarter
            cond_2 = df["reportDate"].dt.year == year
            if df[cond_1 & cond_2]["url"].empty:
                return df["url"].iloc[0]
            else:
                return df[cond_1 & cond_2]["url"].iloc[0]
        elif year:
            return df[df["reportDate"].dt.year == year]["url"].iloc[0]
        else:
            return df["url"].iloc[0]

    def get_list_doc(self, since: datetime, form: str = None):
        df = self.meta[["filingDate", "reportDate", "form", "url"]].copy(deep=True)
        df["reportDate"] = pd.to_datetime(df["reportDate"])
        df = df[df["form"] == form]
        return df[df["reportDate"] >= since]["url"].to_list()
