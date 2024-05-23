class RagUtils:
    def mean_score_filter(rag_results):
        scores = [r.metadata.score for r in rag_results]
        mean_val = sum(scores) / len(scores)
        filtered_docs = list(filter(lambda e: e.metadata.score > mean_val, rag_results))
        return filtered_docs

    def mean_rerank_filter(rag_results):
        scores = [r.metadata.rerank_score for r in rag_results]
        mean_val = sum(scores) / len(scores)
        filtered_docs = list(
            filter(lambda e: e.metadata.rerank_score > mean_val, rag_results)
        )
        return filtered_docs
