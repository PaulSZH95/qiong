from pathlib import Path
import os
from os.path import dirname, join
import convertapi
from dotenv import load_dotenv

script_dir = Path(__file__).absolute()
backend_dir = dirname(dirname(dirname(script_dir)))
secrets_path = join(backend_dir, "config/.env")
load_dotenv(dotenv_path=secrets_path)


class TypeConvert:

    # Code snippet is using the ConvertAPI Python Client: https://github.com/ConvertAPI/convertapi-python
    @staticmethod
    def convert_htm_pdf(
        htm_file_path: str,
        save_to: str,
        type_conv_api: str = None,
        form_format: str = "htm",
    ):
        if not type_conv_api:
            convertapi.api_secret = os.getenv("convertapi_secret")
        status = convertapi.convert(
            "pdf", {"File": htm_file_path}, from_format=form_format
        ).save_files(save_to)
        return status
