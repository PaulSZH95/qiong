import requests
from libraries.edgar_simple.edgar_utils import *
import pandas as pd


class Edgar:

    edgar_configs = sec_config

    @classmethod
    def ticker_to_cik(cls, ticker: str):
        headers = {
            "User-Agent": cls.edgar_configs["browser_agent"],
            "Host": cls.edgar_configs["host"],  # This is another valid field
        }

        response = requests.get(cls.edgar_configs["tickers_url"], headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Code: {response.status_code}, Error: {response.content}")
