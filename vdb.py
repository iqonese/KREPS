"""
Vector Database Module - KREPS Project
Handles storage and retrieval of vector embeddings using ChromaDB
Integrates with Document Ingestion, Chunking, and Vector Embedding modules
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from pathlib import Path
import json
from datetime import datetime


class VectorDatabase:
    """
    Vector Database module using ChromaDB for storing document chunks,
    their embeddings, and metadata from the entire pipeline.
    """

    def __init__(
            self,
            collection_name: str = "kreps_documents",
            persist_directory: str = "./chroma_db"
    ):
        """
        Initialize ChromaDB vector database.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the database
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

        # Get or create collection
        self.collection = self._get_or_create_collection()

        print(f"VectorDatabase initialized")
        print(f"Collection: {collection_name}")
        print(f"Persist directory: {persist_directory}")

    def _get_or_create_collection(self):
        """Get existing collection or create new one."""
        try:
            return self.client.get_collection(name=self.collection_name)
        except:
            return self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

    def store_chunks_with_embeddings(
            self,
            chunks: List,
            embeddings: List[List[float]],
            document_metadata: Dict = None
    ) -> List[str]:
        """
        Store document chunks with their embeddings and metadata.

        Args:
            chunks: List of LangChain Document chunks with metadata
            embeddings: List of embedding vectors (from embedding module)
            document_metadata: Original document metadata from ingestion module

        Returns:
            List of chunk IDs stored in the database
        """
        if not chunks or not embeddings:
            raise ValueError("Chunks and embeddings cannot be empty")

        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch: {len(chunks)} chunks but {len(embeddings)} embeddings")

        chunk_ids = []
        chunk_texts = []
        chunk_metadatas = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"chunk_{self.collection.count() + i}_{int(datetime.now().timestamp())}"
            chunk_ids.append(chunk_id)

            chunk_texts.append(chunk.page_content)

            metadata = {
                "filename": chunk.metadata.get('filename', 'unknown'),
                "page": chunk.metadata.get('page', 0),
                "chunk_index": i,
                "chunk_length": len(chunk.page_content),
                "ingestion_timestamp": datetime.now().isoformat(),
            }

            if document_metadata:
                metadata.update({
                    "doc_language": document_metadata.get('languages', {}),
                    "total_documents": document_metadata.get('total_documents', 0)
                })

            chunk_metadatas.append(metadata)

        self.collection.add(
            ids=chunk_ids,
            documents=chunk_texts,
            embeddings=embeddings,
            metadatas=chunk_metadatas
        )

        print(f"Stored {len(chunk_ids)} chunks in vector database")
        return chunk_ids

    def search_similar_chunks(
            self,
            query_embedding: List[float],
            n_results: int = 5,
            filter_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Search for similar chunks using vector similarity.

        Args:
            query_embedding: Query vector embedding
            n_results: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            Dictionary with chunk IDs, texts, distances, and metadata
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )

        return {
            "ids": results["ids"][0],
            "documents": results["documents"][0],
            "distances": results["distances"][0],
            "metadatas": results["metadatas"][0]
        }

    def get_chunks_by_ids(self, chunk_ids: List[str]) -> Dict:
        """
        Retrieve specific chunks by their IDs.

        Args:
            chunk_ids: List of chunk IDs

        Returns:
            Dictionary with chunk data
        """
        results = self.collection.get(ids=chunk_ids)

        return {
            "ids": results["ids"],
            "documents": results["documents"],
            "metadatas": results["metadatas"]
        }

    def get_chunks_by_document(self, filename: str) -> Dict:
        """
        Retrieve all chunks from a specific document.

        Args:
            filename: Name of the source document

        Returns:
            Dictionary with all chunks from that document
        """
        results = self.collection.get(
            where={"filename": filename}
        )

        return {
            "ids": results["ids"],
            "documents": results["documents"],
            "metadatas": results["metadatas"]
        }

    def delete_chunks(self, chunk_ids: List[str]):
        """Delete specific chunks from the database."""
        self.collection.delete(ids=chunk_ids)
        print(f"Deleted {len(chunk_ids)} chunks")

    def delete_document_chunks(self, filename: str):
        """Delete all chunks from a specific document."""
        self.collection.delete(where={"filename": filename})
        print(f"Deleted all chunks from: {filename}")

    def update_chunk_metadata(self, chunk_id: str, additional_metadata: Dict):
        """
        Update or add metadata to an existing chunk.

        Args:
            chunk_id: ID of the chunk to update
            additional_metadata: New metadata to add/update
        """
        current_data = self.collection.get(ids=[chunk_id])

        if not current_data['ids']:
            raise ValueError(f"Chunk ID not found: {chunk_id}")

        current_metadata = current_data['metadatas'][0]
        updated_metadata = {**current_metadata, **additional_metadata}

        self.collection.update(
            ids=[chunk_id],
            metadatas=[updated_metadata]
        )

        print(f"Updated metadata for chunk: {chunk_id}")

    def update_multiple_chunks_metadata(self, chunk_ids: List[str], additional_metadata: Dict):
        """
        Update metadata for multiple chunks at once.

        Args:
            chunk_ids: List of chunk IDs to update
            additional_metadata: Metadata to add to all chunks
        """
        current_data = self.collection.get(ids=chunk_ids)

        updated_metadatas = []
        for current_meta in current_data['metadatas']:
            updated_meta = {**current_meta, **additional_metadata}
            updated_metadatas.append(updated_meta)

        self.collection.update(
            ids=chunk_ids,
            metadatas=updated_metadatas
        )

        print(f"Updated metadata for {len(chunk_ids)} chunks")

    def add_retrieval_metadata(
            self,
            chunk_id: str,
            query: str,
            similarity_score: float,
            rank: int,
            retrieval_timestamp: str = None
    ):
        """
        Add metadata from the retrieval/context stage.

        Args:
            chunk_id: Chunk that was retrieved
            query: User query that retrieved this chunk
            similarity_score: Similarity score from retrieval
            rank: Rank in retrieval results
            retrieval_timestamp: When it was retrieved
        """
        retrieval_metadata = {
            "last_query": query,
            "last_similarity_score": similarity_score,
            "last_retrieval_rank": rank,
            "last_retrieval_timestamp": retrieval_timestamp or datetime.now().isoformat(),
            "retrieval_count": self._increment_retrieval_count(chunk_id)
        }

        self.update_chunk_metadata(chunk_id, retrieval_metadata)

    def _increment_retrieval_count(self, chunk_id: str) -> int:
        """Helper to track how many times a chunk has been retrieved."""
        current_data = self.collection.get(ids=[chunk_id])
        current_meta = current_data['metadatas'][0]
        current_count = current_meta.get('retrieval_count', 0)
        return current_count + 1

    def add_llm_response_metadata(
            self,
            chunk_ids: List[str],
            response_id: str,
            user_query: str,
            llm_model: str
    ):
        """
        Add metadata from LLM response stage.

        Args:
            chunk_ids: Chunks used for LLM context
            response_id: Unique ID for this response
            user_query: Original user query
            llm_model: Which LLM model was used
        """
        llm_metadata = {
            "used_in_response_id": response_id,
            "response_query": user_query,
            "llm_model": llm_model,
            "llm_timestamp": datetime.now().isoformat()
        }

        self.update_multiple_chunks_metadata(chunk_ids, llm_metadata)
        print(f"Added LLM metadata to {len(chunk_ids)} chunks")

    def get_database_stats(self) -> Dict:
        """Get statistics about the vector database."""
        total_chunks = self.collection.count()

        if total_chunks > 0:
            all_data = self.collection.get()
            unique_docs = set(meta.get('filename', 'unknown')
                              for meta in all_data['metadatas'])
        else:
            unique_docs = set()

        return {
            "collection_name": self.collection_name,
            "total_chunks": total_chunks,
            "unique_documents": len(unique_docs),
            "document_names": list(unique_docs),
            "persist_directory": self.persist_directory
        }

    def reset_database(self):
        """Delete all data from the database."""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"Database '{self.collection_name}' has been reset")

    def export_metadata_to_json(self, output_path: str = "database_metadata.json"):
        """Export all metadata to JSON file."""
        all_data = self.collection.get()

        export_data = {
            "collection_name": self.collection_name,
            "total_chunks": len(all_data['ids']),
            "chunks": []
        }

        for i in range(len(all_data['ids'])):
            export_data["chunks"].append({
                "chunk_id": all_data['ids'][i],
                "metadata": all_data['metadatas'][i],
                "text_preview": all_data['documents'][i][:100] + "..."
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"Metadata exported to: {output_path}")
