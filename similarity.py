"""
Similarity Search Module - KREPS Project
Searches vector database for similar chunks
"""
from typing import Dict
from vdb import VectorDatabase
from embedding import VectorEmbeddingModule


class SimilaritySearch:
    """
    Handles similarity search in vector database.
    """

    def __init__(
            self,
            vector_db: VectorDatabase,
            embedding_module: VectorEmbeddingModule
    ):
        """
        Initialize similarity search module.

        Args:
            vector_db: VectorDatabase instance
            embedding_module: VectorEmbeddingModule instance
        """
        self.vector_db = vector_db
        self.embedding_module = embedding_module

    def search(
            self,
            query: str,
            n_results: int = 14
    ) -> Dict:
        """
        Search for similar chunks in vector database.

        Args:
            query: User query
            n_results: Number of results to return

        Returns:
            Dictionary with search results (ids, documents, distances, metadatas)
        """
        # Generate query embedding
        query_embedding = self.embedding_module.embed_text(query)

        # Search vector database
        results = self.vector_db.search_similar_chunks(
            query_embedding=query_embedding,
            n_results=n_results
        )

        return results
