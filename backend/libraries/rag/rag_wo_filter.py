from pathlib import Path
import time
import os
from os.path import dirname, join

import weaviate
import weaviate.classes.config as wc
from weaviate.classes.query import (
    Rerank,
    MetadataQuery,
)
from dotenv import load_dotenv

script_dir = Path(__file__).absolute()
backend_dir = dirname(dirname(dirname(dirname(script_dir))))
secrets_path = join(backend_dir, "config/.env")
load_dotenv(dotenv_path=secrets_path)


class RagWOFilter:

    def __init__(self, host: str = "weaviate_custom_1", port=8080):
        self.client = weaviate.connect_to_local(
            headers={"X-COHERE-Api-Key": os.getenv("cohere_api")}, host=host, port=port
        )
        self.collections = {}

    def create_collection(self, collection_name: str = "Edgar"):
        if self.client.collections.exists("Edgar"):
            self.client.collections.delete("Edgar")
        self.client.collections.create(
            name=collection_name,
            vectorizer_config=wc.Configure.Vectorizer.text2vec_cohere(
                model="embed-english-v3.0",
                truncate="RIGHT",
            ),
            vector_index_config=wc.Configure.VectorIndex.hnsw(
                distance_metric=wc.VectorDistances.COSINE
            ),
            reranker_config=wc.Configure.Reranker.cohere(model="rerank-english-v2.0"),
            properties=[
                wc.Property(name="content", data_type=wc.DataType.TEXT),
                wc.Property(
                    name="page",
                    data_type=wc.DataType.INT,
                    skip_vectorization=True,
                ),
                wc.Property(
                    name="section_number",
                    data_type=wc.DataType.INT,
                    skip_vectorization=True,
                ),
                wc.Property(
                    name="type",
                    data_type=wc.DataType.TEXT,
                    skip_vectorization=True,
                ),
            ],
        )

    def activate_collection(self, collection_name: str = "Edgar"):
        self.collections[collection_name] = self.client.collections.get(collection_name)
        if self.collections.get(collection_name, None):
            return f"collection name: {collection_name} is activated"

    def update_collection(self, collection_chunks: int, collection_name: str = "Edgar"):
        # Get a collection object for "BlogPost"
        if self.collections.get(collection_name, None):
            pass
        else:
            self.activate_collection(collection_name=collection_name)
        results = self.collections[collection_name].data.insert_many(collection_chunks)
        if results.errors:
            return results.errors
        else:
            return "data is uploaded"

    def rag_qa_hybrid(
        self,
        query_prompt: str,
        limit: int = 10,
        alpha: float = 0.75,
        collection_name: str = "Edgar",
    ):
        response = self.collections[collection_name].query.hybrid(
            query=query_prompt,
            query_properties=["content"],
            return_metadata=MetadataQuery(score=True, explain_score=True),
            alpha=alpha,
            limit=limit,
        )
        return response.objects

    def rag_qa_complex(
        self,
        query_prompt: str,
        rerank_kwargs: dict,
        top_limit: int = 20,
        rank_limit: int = 10,
        collection_name: str = "Edgar",
    ):
        rerank_result = self.collections[collection_name].query.near_text(
            query=query_prompt,
            certainty=0.5,
            limit=top_limit,
            rerank=Rerank(**rerank_kwargs),
            return_metadata=MetadataQuery(certainty=True, distance=True),
            target_vector="content",
        )

        return rerank_result.objects[:rank_limit]

    def close(self):
        try:
            self.client.close()
            time.sleep(5)
            return True
        except:
            return False

    def __str__(self):
        if self.client.is_ready():
            return "Connected to Weaviate"
        else:
            return "Failed to connect to Weaviate"
