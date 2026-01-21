"""
KREPS RAG System - Core Logic
Handles complete RAG pipeline with Qwen 2.5 14B via Ollama
"""

import requests
import atexit
from typing import Dict, List, Optional
from vdb import VectorDatabase
from embedding import VectorEmbeddingModule
from similarity import SimilaritySearch
from retrieval import ContextRetrieval
from prompter import PrompterModule


class QwenRAGSystem:
    """Core RAG system using Qwen 2.5 14B via local Ollama.
    change the ollama url to the url generated in ollama desktop app for your model or changing the model as needed"""

    def __init__(
            self,
            collection_name: str = "kreps_documents",
            ollama_model: str = "qwen3:4b",
            ollama_url: str = "http://localhost:11434",
            top_k: int = 5,
            auto_cleanup: bool = True
    ):
        self.ollama_model = ollama_model
        self.ollama_url = ollama_url
        self.generate_endpoint = f"{ollama_url}/api/generate"
        self.top_k = top_k
        self.collection_name = collection_name
        self.auto_cleanup = auto_cleanup
        self.model = ollama_model

        self.vector_db = VectorDatabase(collection_name=collection_name)
        self.embedding_module = VectorEmbeddingModule()
        self.similarity = SimilaritySearch(self.vector_db, self.embedding_module)
        self.retrieval = ContextRetrieval(self.similarity, top_k=top_k)
        self.prompter = PrompterModule()

        if self.auto_cleanup:
            atexit.register(self.cleanup_on_exit)

    def answer_query(self, query: str, store_scores: bool = True) -> Dict:
        """Main method: Complete pipeline from user query to answer."""
        try:
            contexts = self.retrieval.retrieve_context(query, store_scores=store_scores)

            if not contexts:
                return {
                    'answer': 'No relevant information found in the database.',
                    'query': query,
                    'sources': [],
                    'model': self.ollama_model,
                    'num_chunks': 0
                }

            prompt = self.prompter.augment_prompt(query, contexts)
            answer = self._generate_with_qwen(prompt)

            result = {
                'answer': answer,
                'query': query,
                'sources': [
                    {
                        'filename': ctx['metadata'].get('filename', 'unknown'),
                        'page': ctx['metadata'].get('page', 0),
                        'similarity_score': round(ctx['similarity_score'], 4),
                        'chunk_id': ctx['chunk_id'],
                        'content': ctx['content'][:200] + '...' if len(ctx['content']) > 200 else ctx['content']
                    }
                    for ctx in contexts
                ],
                'model': self.ollama_model,
                'num_chunks': len(contexts)
            }

            return result

        except Exception as e:
            return {
                'answer': f'Error processing query: {str(e)}',
                'query': query,
                'sources': [],
                'model': self.ollama_model,
                'num_chunks': 0,
                'error': str(e)
            }

    def _generate_with_qwen(self, prompt: str) -> str:
        """Generate answer using local Ollama model (e.g., qwen3:4b)."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 2048,
                    "top_p": 0.9,
                    "top_k": 40,
                    "reasoning": False
                }
            }

            response = requests.post(self.generate_endpoint, json=payload, timeout=120)

            # If Ollama returns an error, include the body so you can see why
            if response.status_code != 200:
                return f"Error: Ollama API returned status {response.status_code}: {response.text}"

            # Parse JSON safely
            try:
                data = response.json()
            except Exception:
                return f"Error: Ollama returned non-JSON response: {response.text}"

            # Ollama's response typically contains a "response" field when stream=False
            text = data.get("response")

            # If for some reason we got a streamed-like structure or empty response, surface it
            if not text or not str(text).strip():
                # Sometimes the server might return additional fields worth seeing
                return f"Error: Ollama returned empty/missing 'response'. Raw JSON: {data}"

            return str(text)

        except requests.exceptions.Timeout:
            return "Error: Request timed out. Model is taking too long to respond."

        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Make sure Ollama is running on localhost:11434"

        except Exception as e:
            return f"Error generating answer: {str(e)}"

    def _test_ollama(self) -> bool:
        """Test if Ollama is running and the configured model exists locally."""
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.status_code != 200:
                return False

            data = r.json()
            models = [m.get("name") for m in data.get("models", [])]
            return self.ollama_model in models
        except Exception:
            return False

    def get_stats(self) -> Dict:
        """Get database statistics."""
        return self.vector_db.get_database_stats()

    def health_check(self) -> Dict:
        """Check if all components are working."""
        try:
            ollama_ok = self._test_ollama()
            stats = self.vector_db.get_database_stats()

            return {
                'status': 'healthy' if ollama_ok else 'degraded',
                'ollama': 'connected' if ollama_ok else 'disconnected',
                'database': 'connected',
                'total_chunks': stats['total_chunks'],
                'total_documents': stats['unique_documents'],
                'model': self.ollama_model
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def cleanup_on_exit(self):
        """Delete all data when application exits for security."""
        try:
            self.delete_all_data()
        except Exception as e:
            pass

    def delete_all_data(self):
        """Delete entire collection from ChromaDB."""
        self.vector_db.client.delete_collection(name=self.collection_name)


if __name__ == "__main__":
    rag = QwenRAGSystem(
        collection_name="kreps_documents",
        ollama_model="qwen3:4b",
        top_k=5,
        auto_cleanup=False
    )

    while True:
        query = input("Your question: ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            break

        if not query:
            continue

        result = rag.answer_query(query)
        print(f"\nAnswer: {result['answer']}\n")
