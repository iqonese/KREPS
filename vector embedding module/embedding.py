"""
Vector Embedding Module using ChromaDB and BGE-M3
Provides efficient document storage, retrieval, and semantic search capabilities.
install Flagembedding via `pip install FlagEmbedding`
"""

import chromadb
from chromadb.config import Settings
from FlagEmbedding import BGEM3FlagModel
from typing import List, Dict, Optional, Union
import numpy as np
from pathlib import Path


class VectorEmbeddingModule:
    """
    A comprehensive vector embedding module using ChromaDB and BGE-M3.

    Features:
    - Document embedding and storage
    - Semantic similarity search
    - Batch processing
    - Metadata filtering
    - Persistent storage
    """

    def __init__(
            self,
            collection_name: str = "documents",
            persist_directory: str = "./chroma_db",
            model_name: str = "BAAI/bge-m3"
    ):
        """
        Initialize the vector embedding module.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the database
            model_name: HuggingFace model name for embeddings
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Load BGE-M3 model
        print(f"Loading embedding model: {model_name}")
        self.model = BGEM3FlagModel(model_name, use_fp16=True)
        self.embedding_dim = 1024  # BGE-M3 uses 1024 dimensions

        # Get or create collection
        self.collection = self._get_or_create_collection()

        print(f"VectorEmbeddingModule initialized with collection: {collection_name}")
        print(f"Embedding dimension: {self.embedding_dim}")

    def _get_or_create_collection(self):
        """Get existing collection or create new one."""
        try:
            return self.client.get_collection(name=self.collection_name)
        except Exception:
            return self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

    def embed_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text using BGE-M3.

        Args:
            text: Single text string or list of texts

        Returns:
            numpy array of embeddings
        """
        if isinstance(text, str):
            text = [text]

        # FlagEmbedding returns dense vectors
        results = self.model.encode(text, return_dense=True, return_sparse=False, return_colbert=False,normalize_embeddings=True)
        embeddings = np.array(results['dense_vecs'])

        return embeddings



    def add_documents(
            self,
            documents: List[str],
            metadatas: Optional[List[Dict]] = None,
            ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to the collection.

        Args:
            documents: List of document texts
            metadatas: Optional list of metadata dictionaries
            ids: Optional list of document IDs (auto-generated if not provided)

        Returns:
            List of document IDs
        """
        if not documents:
            raise ValueError("Documents list cannot be empty")

        # Generate IDs if not provided
        if ids is None:
            existing_count = self.collection.count()
            ids = [f"doc_{existing_count + i}" for i in range(len(documents))]

        # Generate embeddings
        embeddings = self.embed_text(documents)

        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            ids=ids
        )

        print(f"Added {len(documents)} documents to collection")
        return ids

    def search(
            self,
            query: str,
            n_results: int = 5,
            where: Optional[Dict] = None,
            where_document: Optional[Dict] = None
    ) -> Dict:
        """
        Semantic search for similar documents.

        Args:
            query: Search query text
            n_results: Number of results to return
            where: Metadata filter (e.g., {"category": "science"})
            where_document: Document content filter

        Returns:
            Dictionary with ids, documents, distances, and metadatas
        """
        # Generate query embedding
        query_embedding = self.embed_text(query)[0]

        # Search collection
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where,
            where_document=where_document
        )

        return {
            "ids": results["ids"][0],
            "documents": results["documents"][0],
            "distances": results["distances"][0],
            "metadatas": results["metadatas"][0] if results["metadatas"][0] else None
        }

    def batch_search(
            self,
            queries: List[str],
            n_results: int = 5
    ) -> List[Dict]:
        """
        Perform batch semantic search.

        Args:
            queries: List of search queries
            n_results: Number of results per query

        Returns:
            List of result dictionaries
        """
        query_embeddings = self.embed_text(queries)

        results = self.collection.query(
            query_embeddings=query_embeddings.tolist(),
            n_results=n_results
        )

        batch_results = []
        for i in range(len(queries)):
            batch_results.append({
                "query": queries[i],
                "ids": results["ids"][i],
                "documents": results["documents"][i],
                "distances": results["distances"][i],
                "metadatas": results["metadatas"][i] if results["metadatas"][i] else None
            })

        return batch_results

    def get_documents(self, ids: List[str]) -> Dict:
        """
        Retrieve specific documents by IDs.

        Args:
            ids: List of document IDs

        Returns:
            Dictionary with documents and metadatas
        """
        results = self.collection.get(ids=ids)

        return {
            "ids": results["ids"],
            "documents": results["documents"],
            "metadatas": results["metadatas"]
        }

    def update_document(
            self,
            doc_id: str,
            document: Optional[str] = None,
            metadata: Optional[Dict] = None
    ):
        """
        Update a document's content or metadata.

        Args:
            doc_id: Document ID to update
            document: New document text (optional)
            metadata: New metadata (optional)
        """
        update_kwargs = {"ids": [doc_id]}

        if document is not None:
            embedding = self.embed_text(document)[0]
            update_kwargs["documents"] = [document]
            update_kwargs["embeddings"] = [embedding.tolist()]

        if metadata is not None:
            update_kwargs["metadatas"] = [metadata]

        self.collection.update(**update_kwargs)
        print(f"Updated document: {doc_id}")

    def delete_documents(self, ids: List[str]):
        """
        Delete documents from collection.

        Args:
            ids: List of document IDs to delete
        """
        self.collection.delete(ids=ids)
        print(f"Deleted {len(ids)} documents")

    def get_collection_info(self) -> Dict:
        """
        Get information about the collection.

        Returns:
            Dictionary with collection statistics
        """
        count = self.collection.count()

        return {
            "name": self.collection_name,
            "document_count": count,
            "embedding_dimension": self.embedding_dim,
            "persist_directory": self.persist_directory
        }

    def reset_collection(self):
        """Delete all documents from the collection."""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"Collection '{self.collection_name}' has been reset")


# Example usage
if __name__ == "__main__":
    # Initialize the module
    vem = VectorEmbeddingModule(
        collection_name="my_documents",
        persist_directory="./vector_db"
    )

    # Sample documents
    documents = [
        "Artificial intelligence is transforming technology.",
        "Machine learning models require large datasets.",
        "Python is a popular programming language.",
        "Natural language processing enables text understanding.",
        "Deep learning uses neural networks with multiple layers."
    ]

    metadatas = [
        {"category": "AI", "date": "2024-01"},
        {"category": "ML", "date": "2024-01"},
        {"category": "Programming", "date": "2024-02"},
        {"category": "NLP", "date": "2024-02"},
        {"category": "Deep Learning", "date": "2024-03"}
    ]

    # Add documents
    doc_ids = vem.add_documents(documents, metadatas=metadatas)

    # Search for similar documents
    query = "What is deep learning?"
    results = vem.search(query, n_results=3)

    print(f"\nSearch results for: '{query}'")
    print("-" * 50)
    for i, (doc, dist, meta) in enumerate(zip(
            results["documents"],
            results["distances"],
            results["metadatas"]
    )):
        print(f"{i + 1}. Distance: {dist:.4f}")
        print(f"   Document: {doc}")
        print(f"   Metadata: {meta}")
        print()

    # Get collection info
    info = vem.get_collection_info()
    print(f"\nCollection Info: {info}")