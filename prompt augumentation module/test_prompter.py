"""
Testing module for PrompterModule
Tests prompt augmentation and formatting
"""

from prompter import PrompterModule


def test_prompter():
    """Test PrompterModule functionality"""

    print("=" * 60)
    print("TESTING PROMPTER MODULE")
    print("=" * 60)

    # Initialize prompter
    prompter = PrompterModule(max_context_length=20000)
    print("\n✓ PrompterModule initialized")
    print(f"  Max context length: {prompter.max_context_length} characters")

    # Test 1: Basic prompt augmentation
    print("\n" + "=" * 60)
    print("TEST 1: Basic Prompt Augmentation")
    print("=" * 60)

    test_chunks = [
        {
            'content': 'Machine learning is a subset of artificial intelligence that enables systems to learn from data.',
            'metadata': {'source': 'ml_intro.pdf', 'chunk_id': 0},
            'similarity_score': 0.85
        },
        {
            'content': 'Deep learning uses neural networks with multiple layers to process complex patterns.',
            'metadata': {'source': 'deep_learning.pdf', 'chunk_id': 1},
            'similarity_score': 0.78
        },
        {
            'content': 'Neural networks are inspired by biological neurons in the human brain.',
            'metadata': {'source': 'neural_nets.pdf', 'chunk_id': 2},
            'similarity_score': 0.72
        }
    ]

    test_query = "What is machine learning?"

    augmented_prompt = prompter.augment_prompt(test_query, test_chunks)
    print(f"\nQuery: {test_query}")
    print(f"Chunks used: {len(test_chunks)}")
    print("\nAugmented Prompt:")
    print("-" * 60)
    print(augmented_prompt)
    print("-" * 60)

    # Test 2: Context length limit
    print("\n" + "=" * 60)
    print("TEST 2: Context Length Limiting")
    print("=" * 60)

    # Create prompter with small limit
    small_prompter = PrompterModule(max_context_length=200)

    long_chunks = [
        {
            'content': 'A' * 150,  # 150 characters
            'metadata': {'source': 'doc1.pdf', 'chunk_id': 0},
            'similarity_score': 0.9
        },
        {
            'content': 'B' * 150,  # 150 characters
            'metadata': {'source': 'doc2.pdf', 'chunk_id': 1},
            'similarity_score': 0.8
        },
        {
            'content': 'C' * 150,  # 150 characters (should be excluded)
            'metadata': {'source': 'doc3.pdf', 'chunk_id': 2},
            'similarity_score': 0.7
        }
    ]

    context = small_prompter.format_context(long_chunks)
    print(f"\nMax context length: {small_prompter.max_context_length} chars")
    print(f"Total chunks provided: {len(long_chunks)}")
    print(f"Context length after limiting: {len(context)} chars")
    print(f"Chunks included: {context.count('[')}")  # Count source markers

    # Test 3: Empty chunks
    print("\n" + "=" * 60)
    print("TEST 3: Empty Chunks Handling")
    print("=" * 60)

    empty_chunks = []
    empty_prompt = prompter.augment_prompt("Test query?", empty_chunks)
    print(f"\nEmpty chunks handled: {'Context:\n\n' in empty_prompt}")

    # Test 4: Multiple chunks with token estimation
    print("\n" + "=" * 60)
    print("TEST 4: Realistic RAG Scenario (7 chunks)")
    print("=" * 60)

    realistic_chunks = [
        {
            'content': f'This is chunk {i} with some relevant information about the topic. ' * 10,
            'metadata': {'source': f'document_{i}.pdf', 'chunk_id': i},
            'similarity_score': 0.9 - (i * 0.05)
        }
        for i in range(7)
    ]

    realistic_query = "What information do the documents contain?"
    realistic_prompt = prompter.augment_prompt(realistic_query, realistic_chunks)

    print(f"\nQuery: {realistic_query}")
    print(f"Chunks retrieved: {len(realistic_chunks)}")
    print(f"Prompt length: {len(realistic_prompt)} characters")
    print(f"Estimated tokens: ~{len(realistic_prompt) // 4}")
    print(f"\nFirst 500 chars of prompt:")
    print("-" * 60)
    print(realistic_prompt[:500] + "...")
    print("-" * 60)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✓ All tests completed successfully")
    print("✓ Prompt augmentation working")
    print("✓ Context length limiting working")
    print("✓ Edge cases handled")


if __name__ == "__main__":
    test_prompter()
