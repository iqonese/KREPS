"""
Context Retrieval Module - KREPS Project
Retrieves and formats relevant context for LLM
"""

from typing import List, Dict
from similarity import SimilaritySearch


class ContextRetrieval:
    def __init__(self, similarity_search: SimilaritySearch, top_k: int = 6):
        self.similarity_search = similarity_search
        self.top_k = top_k

    def retrieve_context(
            self,
            query: str,
            top_k: int = None,
            store_scores: bool = True
    ) -> List[Dict]:
        k = top_k or self.top_k
        initial_results = k * 2
        results = self.similarity_search.search(query, n_results=initial_results)

        contexts = []
        for i in range(len(results['ids'])):
            context = {
                'chunk_id': results['ids'][i],
                'content': results['documents'][i],  # FIXED
                'similarity_score': 1 - results['distances'][i],
                'metadata': results['metadatas'][i],
                'rank': i + 1
            }
            contexts.append(context)

        contexts.sort(key=lambda x: x['similarity_score'], reverse=True)
        top_contexts = contexts[:k]

        # NEW: Store similarity scores
        if store_scores:
            vector_db = self.similarity_search.vector_db
            for ctx in top_contexts:
                try:
                    vector_db.add_retrieval_metadata(
                        chunk_id=ctx['chunk_id'],
                        query=query,
                        similarity_score=ctx['similarity_score'],
                        rank=ctx['rank']
                    )
                except Exception as e:
                    print(f"Warning: Could not store metadata for {ctx['chunk_id']}: {e}")

        return top_contexts

