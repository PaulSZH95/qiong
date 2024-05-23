import yaml
from pathlib import Path
import os
from os.path import dirname, join
from datetime import datetime, timedelta

import numpy as np
from dotenv import load_dotenv
from groq import Groq

script_dir = Path(__file__).absolute()
backend_dir = dirname(dirname(dirname(dirname(script_dir))))
llm_configs_path = join(backend_dir, "assets/llm_configs.yaml")
secrets_path = join(backend_dir, "config/.env")
load_dotenv(dotenv_path=secrets_path)
os.environ["GROQ_API_KEY"] = os.getenv("groq")

with open(llm_configs_path, "r", encoding="UTF-8") as file:
    llm_configs = yaml.safe_load(file)


class Groq:

    client = Groq()

    def __init__(self, **kwargs):
        try:
            self.model = llm_configs["models"][kwargs.get("model", "groq_llama")]
        except:
            self.model = "groq_llama"
        self.temperature = kwargs.get("temp", 0)
        self.top_p = kwargs.get("top_p", 1)
        self.seed = kwargs.get("seed", 24)

    def simple_inferencing(self, content):
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"{content}",
                }
            ],
            model=llm_configs["models"][self.model],
            temperature=self.temperature,
            top_p=self.top_p,
            seed=self.seed,
        )
        return chat_completion.choices[0].message.content
