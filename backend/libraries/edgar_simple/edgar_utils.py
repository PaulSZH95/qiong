import yaml
from pathlib import Path
from os.path import dirname, join
from datetime import datetime, timedelta
import numpy as np

script_dir = Path(__file__).absolute()
asset_dir = dirname(dirname(dirname(script_dir)))
sec_config_path = join(
    asset_dir, "assets/sec_config.yaml"
)  # can become dynamic too by using a yaml with config paths

with open(sec_config_path, "r", encoding="UTF-8") as file:
    sec_config = yaml.safe_load(file)


class EdgarUtils:

    @classmethod
    def edgar_cur_to_dates(cls, meta_dict: dict):
        last_date = meta_dict["filings"]["recent"]["filingDate"][-1]
        up_to_dates = [datetime.strptime(last_date, "%Y-%m-%d")]
        urls = [None]
        for file in meta_dict["filings"]["files"]:
            up_to_dates.append(datetime.strptime(file["filingFrom"], "%Y-%m-%d"))
            urls.append(file["name"])
        return np.array(up_to_dates), np.array(urls)

    @classmethod
    def redo_edgar_by_date(
        cls, up_to_dates: np.array, urls: np.array, date_filter: datetime
    ):
        if urls[np.where(up_to_dates <= date_filter)][0]:
            new_url = (
                sec_config["meta_url"] + urls[np.where(up_to_dates <= date_filter)][0]
            )
        else:
            new_url = None
        return new_url

    @staticmethod
    def parse_url_to_doc():
        pass


__all__ = ["sec_config", "EdgarUtils"]
