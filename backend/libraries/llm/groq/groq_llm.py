import yaml
from pathlib import Path
import os
from os.path import dirname, join
from datetime import datetime, timedelta

import numpy as np
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from libraries.llm.groq.struct_out import SectionTags

script_dir = Path(__file__).absolute()
backend_dir = dirname(dirname(dirname(dirname(script_dir))))
llm_configs_path = join(backend_dir, "assets/llm_configs.yaml")
secrets_path = join(backend_dir, "config/.env")
load_dotenv(dotenv_path=secrets_path)
os.environ["GROQ_API_KEY"] = os.getenv("groq")

with open(llm_configs_path, "r", encoding="UTF-8") as file:
    llm_configs = yaml.safe_load(file)


class Groq:

    def __init__(self, **kwargs):
        try:
            self.model = llm_configs["models"][kwargs.get("model", "groq_llama")]
        except:
            self.model = "groq_llama"
        self.temperature = kwargs.get("temp", 0)
        self.top_p = kwargs.get("top_p", 1)
        self.seed = kwargs.get("seed", 24)

    @property
    def client(self):
        model_kwargs = {"top_p": self.top_p, "seed": self.seed}
        chat = ChatGroq(
            temperature=self.temperature,
            model_name=self.model,
            model_kwargs=model_kwargs,
        )
        return chat

    def simple_inferencing(self, content):
        system = "You are a helpful assistant."
        human = "{text}"
        prompt = ChatPromptTemplate.from_messages(
            [("system", system), ("human", human)]
        )

        chain = prompt | self.client
        return chain.invoke({"text": content})

    def struct_output(self, content):
        struct_llm = self.client.with_structured_output(SectionTags)
        return struct_llm.invoke(content)
