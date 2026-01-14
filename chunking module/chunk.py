from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from pathlib import Path


def process_document(file_path, chunk_size=500, chunk_overlap=100):
    """
    Load and chunk a single PDF or DOCX file

    Args:
        file_path: Path to the document
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks

    Returns:
        List of document chunks with metadata
    """
    file_extension = os.path.splitext(file_path)[1].lower()

    # Load document based on file type
    if file_extension == '.pdf':
        loader = PyPDFLoader(file_path)
    elif file_extension in ['.docx', '.doc']:
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

    # Load the document
    documents = loader.load()

    # Create text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    # Split into chunks
    chunks = text_splitter.split_documents(documents)

    # Add filename to metadata
    filename = os.path.basename(file_path)
    for chunk in chunks:
        chunk.metadata['filename'] = filename

    return chunks


def process_directory(directory_path, chunk_size=500, chunk_overlap=100):
    """
    Process all PDFs and DOCX files in a directory

    Args:
        directory_path: Path to directory containing documents
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks

    Returns:
        List of all document chunks from all files
    """
    all_chunks = []

    # Get all PDF and DOCX files
    directory = Path(directory_path)
    file_patterns = ['*.pdf', '*.docx', '*.doc']

    files = []
    for pattern in file_patterns:
        files.extend(directory.glob(pattern))

    print(f"Found {len(files)} documents to process")

    # Process each file
    for file_path in files:
        print(f"Processing {file_path.name}...")

        try:
            chunks = process_document(
                str(file_path),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            all_chunks.extend(chunks)
            print(f"  ✓ Created {len(chunks)} chunks")

        except Exception as e:
            print(f"  ✗ Error processing {file_path.name}: {e}")

    return all_chunks


def get_chunk_statistics(chunks):
    """
    Get statistics about the chunks

    Args:
        chunks: List of document chunks

    Returns:
        Dictionary with statistics
    """
    if not chunks:
        return {"total_chunks": 0}

    chunk_lengths = [len(chunk.page_content) for chunk in chunks]

    # Get unique source files
    sources = set(chunk.metadata.get('filename', 'unknown') for chunk in chunks)

    stats = {
        "total_chunks": len(chunks),
        "total_documents": len(sources),
        "avg_chunk_length": sum(chunk_lengths) / len(chunk_lengths),
        "min_chunk_length": min(chunk_lengths),
        "max_chunk_length": max(chunk_lengths),
        "sources": list(sources)
    }

    return stats


def save_chunks_to_file(chunks, output_file="chunks_output.txt"):
    """
    Save chunks to a text file for inspection

    Args:
        chunks: List of document chunks
        output_file: Path to output file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, chunk in enumerate(chunks):
            f.write(f"{'=' * 80}\n")
            f.write(f"CHUNK {i + 1}\n")
            f.write(f"Source: {chunk.metadata.get('filename', 'unknown')}\n")
            f.write(f"Page: {chunk.metadata.get('page', 'N/A')}\n")
            f.write(f"Length: {len(chunk.page_content)} characters\n")
            f.write(f"{'=' * 80}\n")
            f.write(chunk.page_content)
            f.write(f"\n\n")

    print(f"Chunks saved to {output_file}")


# Example usage
if __name__ == "__main__":
    # Process a single document
    print("Example 1: Process single document")
    print("-" * 80)
    single_chunks = process_document("example.pdf")
    print(f"Created {len(single_chunks)} chunks from single document\n")

    # Process all documents in a directory
    print("Example 2: Process directory of documents")
    print("-" * 80)
    all_chunks = process_directory("./documents", chunk_size=500, chunk_overlap=200)

    # Get statistics
    stats = get_chunk_statistics(all_chunks)
    print(f"\nStatistics:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Average chunk length: {stats['avg_chunk_length']:.0f} characters")
    print(f"  Min/Max chunk length: {stats['min_chunk_length']}/{stats['max_chunk_length']}")

    # Save chunks to file for inspection
    save_chunks_to_file(all_chunks, "chunks_output.txt")

    # Print first chunk as example
    if all_chunks:
        print(f"\nFirst chunk preview:")
        print("-" * 80)
        print(f"Source: {all_chunks[0].metadata.get('filename')}")
        print(f"Content: {all_chunks[0].page_content[:300]}...")