"""
Prompt Augmentation Module
Formats retrieved context and user query into structured prompt for LLM
"""

from langchain.prompts import PromptTemplate
from typing import List, Dict


class PrompterModule:
    """Handles prompt construction for RAG pipeline"""

    def __init__(self, max_context_length: int = 20000):
        """
        Initialize prompter module

        Args:
            max_context_length: Maximum characters for context
                              (default: 20000 chars ~5000 tokens)
        """
        self.max_context_length = max_context_length
        self.template = self._create_template()

    def _create_template(self) -> PromptTemplate:
        """Create RAG prompt template"""
        template = """You are a helpful AI assistant. Answer the question based on the provided context.

Context:
{context}

Question: {question}

Answer: Provide a clear, accurate answer based only on the context above. If the context doesn't contain relevant information, say so."""

        return PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )

    def format_context(self, retrieved_chunks: List[Dict]) -> str:
        """
        Format retrieved chunks into context string

        Args:
            retrieved_chunks: List of chunks from ContextRetrieval

        Returns:
            Formatted context string
        """
        context_parts = []
        total_length = 0

        for i, chunk in enumerate(retrieved_chunks, 1):
            # Match structure from contextretrieval.py
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            source = metadata.get('source', 'Unknown')

            part = f"[{i}] Source: {source}\n{content}\n"

            # Check if adding this chunk exceeds limit
            if total_length + len(part) > self.max_context_length:
                break

            context_parts.append(part)
            total_length += len(part)

        return "\n".join(context_parts)

    def augment_prompt(self, query: str, retrieved_chunks: List[Dict]) -> str:
        """
        Create augmented prompt from query and retrieved chunks

        Args:
            query: User question (string)
            retrieved_chunks: Retrieved context chunks from ContextRetrieval

        Returns:
            Formatted prompt string ready for LLM
        """
        context = self.format_context(retrieved_chunks)
        prompt = self.template.format(context=context, question=query)
        return prompt
