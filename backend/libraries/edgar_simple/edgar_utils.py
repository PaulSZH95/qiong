import yaml
from pathlib import Path
from os.path import dirname, join

script_dir = Path(__file__).absolute()
asset_dir = dirname(dirname(dirname(script_dir)))
sec_config_path = join(
    asset_dir, "assets/sec_config.yaml"
)  # can become dynamic too by using a yaml with config paths

with open(sec_config_path, "r", encoding="UTF-8") as file:
    sec_config = yaml.safe_load(file)

__all__ = ["sec_config"]
