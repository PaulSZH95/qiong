import requests
from libraries.edgar_simple.edgar_utils import *


class RedirectUtils:

    sec_meta_headers = sec_config["sec_meta_headers"]
    tick_to_cik_headers = sec_config["tick_to_cik_headers"]

    @classmethod
    def new_meta_data(cls, url: str):
        response = requests.get(url, headers=cls.sec_meta_headers, timeout=120)
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            raise ValueError(f"Code: {response.status_code}, Error: {response.reason}")

    @classmethod
    def query_url(cls, url: str):
        response = requests.get(url, headers=cls.tick_to_cik_headers, timeout=120)
        if response.status_code == 200:
            result = response.text
            return result
        else:
            raise ValueError(f"Code: {response.status_code}, Error: {response.reason}")
