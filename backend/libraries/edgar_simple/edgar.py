import requests
from libraries.edgar_simple.edgar_utils import *
import pandas as pd
from typing import List


class EdgarData:

    tick_to_cik_headers = sec_config["tick_to_cik_headers"]
    sec_meta_headers = sec_config["sec_meta_headers"]

    @classmethod
    def _get_cik(cls, list_of_cik_tick: List[dict], ticker: str):
        df_tick = pd.DataFrame(list_of_cik_tick)
        return df_tick[df_tick["ticker"] == ticker]["cik_str"].item()

    @classmethod
    def ticker_to_cik(cls, ticker: str):
        response = requests.get(
            sec_config["tickers_url"], headers=cls.tick_to_cik_headers, timeout=120
        )
        if response.status_code == 200:
            result = response.json()
            return cls._get_cik(result.values(), ticker)
        else:
            raise ValueError(f"Code: {response.status_code}, Error: {response.reason}")

    @classmethod
    def cik_serialization(cls, cik: str):
        if isinstance(cik, int):
            cik = str(cik)
        if (
            len(cik) <= sec_config["cik_filler"] - 3
        ):  # CIK + cik needs to be len of cik_length as defined by sec
            cik_padded = "CIK" + "0" * (sec_config["cik_filler"] - 3 - len(cik)) + cik
            return cik_padded
        else:
            raise ValueError(
                f'SEC has hard requirement of cik serialisation. Length of CIK{cik} is not within length of {sec_config["cik_filler"]}'
            )

    @classmethod
    def _get_meta_data_url(cls, cik_serial: str):
        meta_data_url = (
            sec_config["meta_url"] + cik_serial + sec_config["meta_url_extension"]
        )
        return meta_data_url

    @classmethod
    def get_meta_data(cls, cik_serial: str):
        meta_data_url = cls._get_meta_data_url(cik_serial)
        response = requests.get(
            meta_data_url, headers=cls.sec_meta_headers, timeout=120
        )
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            raise ValueError(f"Code: {response.status_code}, Error: {response.reason}")
