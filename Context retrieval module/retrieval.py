"""
Context Retrieval Module - KREPS Project
Retrieves and formats relevant context for LLM
"""
from typing import List, Dict
from similarity_search import SimilaritySearch

class ContextRetrieval:
    """
    Retrieves and formats context from similarity search results.
    """

    def __init__(
            self,
            similarity_search: SimilaritySearch,
            top_k: int = 7
    ):
        """
        Initialize context retrieval module.

        Args:
            similarity_search: SimilaritySearch instance
            top_k: Number of top chunks to return
        """
        self.similarity_search = similarity_search
        self.top_k = top_k

    def retrieve_context(
            self,
            query: str,
            top_k: int = None
    ) -> List[Dict]:
        """
        Retrieve and format relevant context for a query.

        Args:
            query: User query
            top_k: Override default top_k

        Returns:
            List of formatted context chunks
        """
        k = top_k or self.top_k

        # Get results from similarity search (get 2x for better selection)
        initial_results = k * 2
        results = self.similarity_search.search(query, n_results=initial_results)

        # Format results
        contexts = []
        for i in range(len(results['ids'])):
            context = {
                'chunk_id': results['ids'][i],
                'text': results['documents'][i],
                'similarity_score': 1 - results['distances'][i],
                'metadata': results['metadatas'][i],
                'rank': i + 1
            }
            contexts.append(context)

        # Sort by similarity score to ensure best chunks
        contexts.sort(key=lambda x: x['similarity_score'], reverse=True)

        # Return top K chunks
        return contexts[:k]
