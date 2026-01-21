"""
KREPS RAG System - Main Entry Point
Orchestrates all modules: ingestion pipeline and RAG query system
"""
import os
import sys
from chunk import process_directory
from vdb import VectorDatabase
from embedding import VectorEmbeddingModule
from rag import QwenRAGSystem


def run_ingestion_pipeline(folder_path: str, collection_name: str = "kreps_documents"):
    """
    Orchestrates complete ingestion pipeline.
    Connects: Chunking -> Embedding -> VectorDB
    """
    # Initialize modules
    embedding_module = VectorEmbeddingModule()
    vector_db = VectorDatabase(collection_name=collection_name)

    # Step 1: Chunk documents
    chunks = process_directory(folder_path, chunk_size=500, chunk_overlap=100)
    if not chunks:
        print("ERROR: No documents found")
        return False

    # Step 2: Generate embeddings
    chunk_texts = [chunk.page_content for chunk in chunks]
    embeddings = embedding_module.embed_documents(chunk_texts)

    # Step 3: Store in vector database
    vector_db.store_chunks_with_embeddings(
        chunks=chunks,
        embeddings=embeddings
    )

    stats = vector_db.get_database_stats()
    print(f"Ingestion complete: {stats['total_chunks']} chunks from {stats['unique_documents']} documents")
    return True


def run_query_mode(collection_name: str = "kreps_documents"):
    """
    Interactive CLI for testing RAG system.
    """
    rag = QwenRAGSystem(
        collection_name=collection_name,
        ollama_model="qwen3:4b",
        top_k=5,
        auto_cleanup=False
    )

    health = rag.health_check()
    if health['status'] != 'healthy':
        print("WARNING: Ollama not running. Start with: ollama serve")

    print("Enter question (or 'quit' to exit)\n")

    while True:
        try:
            query = input("Question: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                break

            if not query:
                continue

            result = rag.answer_query(query)

            print(f"\nAnswer: {result['answer']}\n")
            print(f"Sources ({result['num_chunks']} chunks):")
            for i, source in enumerate(result['sources'], 1):
                print(f"  [{i}] {source['filename']} (Page {source['page']}, Score: {source['similarity_score']:.4f})")
            print()

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"ERROR: {str(e)}")


def run_api_server():
    """
    Launch Flask API server for frontend integration.
    """
    print("Starting API server on http://localhost:5000\n")
    from api import app
    app.run(host='0.0.0.0', port=5000, debug=True)


def main():
    """
    Entry point: provides three operational modes.
    """
    print("\nKREPS RAG SYSTEM")
    print("1. Ingest documents")
    print("2. Query mode")
    print("3. Run API server")
    print("4. Exit\n")

    choice = input("Choose (1-4): ").strip()

    match choice:
        case "1":
            folder = input("Folder path: ").strip()
            if os.path.exists(folder):
                run_ingestion_pipeline(folder)
            else:
                print("ERROR: Folder not found")

        case "2":
            run_query_mode()

        case "3":
            run_api_server()

        case "4":
            sys.exit(0)

        case _:
            print("Invalid choice")


if __name__ == "__main__":
    main()
