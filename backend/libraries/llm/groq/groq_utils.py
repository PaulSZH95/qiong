import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter


def approx_token_counter(prompt):
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(prompt))


def split_text(prompt):
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        model_name="gpt-4",
        chunk_size=250,
        chunk_overlap=50,
    )
    return text_splitter.split_text(prompt)
