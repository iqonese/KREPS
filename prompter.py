"""
Prompt Augmentation Module
Formats retrieved context and user query into structured prompt for LLM
"""

from langchain.prompts import PromptTemplate
from typing import List, Dict

class PrompterModule:
    """Handles prompt construction for RAG pipeline"""

    def __init__(self, max_context_tokens: int = 5000):
        """
        Initialize prompter module

        Args:
            max_context_tokens: Maximum tokens for context
        """
        self.max_context_tokens = max_context_tokens
        self.template = self._create_template()

    def _create_template(self) -> PromptTemplate:
        """Create RAG prompt template"""
        template = """You are a factual assistant.
        Answer the question using ONLY the provided context.

        Style:
        - Write a complete answer in a short paragraph (about 4–8 sentences).
        - Do NOT explain your reasoning or how you arrived at the answer.
        - Include important details from the context (names, numbers, dates) when relevant.
        - If the answer is not explicitly stated in the context, say:
          "I don't know based on the provided context."

        Context:
        {context}

        Question: {question}

        Answer:
        """

        return PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count from text

        Args:
            text: Input text string

        Returns:
            Estimated token count
        """
        return max(len(text) // 4, len(text.split()))

    def format_context(self, retrieved_chunks: List[Dict]) -> str:
        """
        Format retrieved chunks into context string

        Args:
            retrieved_chunks: List of chunks from ContextRetrieval

        Returns:
            Formatted context string
        """
        context_parts = []
        total_tokens = 0


        for i, chunk in enumerate(retrieved_chunks, 1):
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            filename = metadata.get("filename", metadata.get("source", "Unknown"))
            page = metadata.get("page", None)
            page_str = f", Page: {page}" if page is not None else ""
            part = f"[{i}] Source: {filename}{page_str}\n{content}\n"
            part_tokens = self._estimate_tokens(part)

            if total_tokens + part_tokens > self.max_context_tokens:
                break

            context_parts.append(part)
            total_tokens += part_tokens

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

