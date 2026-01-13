from langchain.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splwhichitter import RecursiveCharacterTextSplitter
import os


def process_document(file_path):
    """Load and chunk a PDF or DOCX file"""

    # Determine file type and load accordingly
    file_extension = os.path.splitext(file_path)[1].lower()

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
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    # Split into chunks
    chunks = text_splitter.split_documents(documents)

    return chunks


# Usage
chunks = process_document("document.pdf")
print(f"Created {len(chunks)} chunks")
print(f"First chunk: {chunks[0].page_content[:200]}...")