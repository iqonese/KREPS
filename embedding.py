"""
Vector Embedding Module - KREPS Project
Generates embeddings using BGE-M3 model
"""

from FlagEmbedding import BGEM3FlagModel
from typing import List, Union
import numpy as np


class VectorEmbeddingModule:
    """
    Handles conversion of text to vector embeddings using BGE-M3.
    This module ONLY does embedding - storage is handled by vdb.py
    """

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        """
        Initialize the BGE-M3 embedding model.

        Args:
            model_name: HuggingFace model name for embeddings
        """
        print(f"Loading embedding model: {model_name}")
        self.model = BGEM3FlagModel(model_name, use_fp16=False)
        self.embedding_dim = 1024  # BGE-M3 uses 1024 dimensions
        print(f"VectorEmbeddingModule initialized")
        print(f"Embedding dimension: {self.embedding_dim}")

    def embed_text(self, text):
        results = self.model.encode(
            text,
            batch_size=32,
            max_length=512
        )

        # BGEM3FlagModel.encode may return a dict
        if isinstance(results, dict):
            results = results.get("dense_vecs")

        if results is None:
            raise ValueError("Embedding model returned no dense_vecs output")

        return results.tolist() if hasattr(results, "tolist") else results

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Convenience method to embed multiple documents and return as list.

        Args:
            documents: List of document text strings

        Returns:
            List of embeddings (each embedding is a list of 1024 floats)
        """
        embeddings = self.embed_text(documents)
        return embeddings
