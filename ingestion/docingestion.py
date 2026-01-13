import os
import re
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path
import time
import hashlib

import PyPDF2
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0

@dataclass
class Document:
    doc_id: str
    file_name: str
    file_type: str
    content: str
    language: str
    file_size: int
    file_path: str
    metadata: dict


class DocumentIngestion:

    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.txt']

    def process_documents(self, file_paths: List[str]) -> tuple[List[Document], dict]:
        """
        Process uploaded documents and return documents list with metadata.
        Args:
            file_paths: List of file paths uploaded by user
        Returns:
            tuple: (list of Document objects, metadata dictionary)
        """
        documents = []

        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue

            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                continue

            try:
                file_name = os.path.basename(file_path)

                if file_ext == '.pdf':
                    doc = self._process_pdf(file_path, file_name)
                elif file_ext == '.docx':
                    doc = self._process_docx(file_path, file_name)
                elif file_ext == '.txt':
                    doc = self._process_txt(file_path, file_name)
                else:
                    continue

                if doc:
                    documents.append(doc)
            except:
                continue

        metadata = self._generate_metadata(documents)
        return documents, metadata

    def _process_pdf(self, file_path: str, file_name: str) -> Optional[Document]:
        text_content = self._extract_text_from_pdf(file_path)

        if not text_content.strip():
            return None

        cleaned_text = self._clean_text(text_content)
        language = self._detect_language(cleaned_text)
        file_size = os.path.getsize(file_path)
        doc_id = self._generate_doc_id(file_name)

        metadata = {
            "source": "pdf",
            "file_size_bytes": file_size
        }

        return Document(
            doc_id=doc_id,
            file_name=file_name,
            file_type='pdf',
            content=cleaned_text,
            language=language,
            file_size=file_size,
            file_path=file_path,
            metadata=metadata
        )

    def _extract_text_from_pdf(self, file_path: str) -> str:
        text_content = ""
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
        return text_content

    def _process_docx(self, file_path: str, file_name: str) -> Optional[Document]:
        #from docx import Document as DocxDocument
        #
        # text_content = ""
        # doc_obj = DocxDocument(file_path)
        #
        # for paragraph in doc_obj.paragraphs:
        #     text_content += paragraph.text + "\n"
        #
        # for table in doc_obj.tables:
        #     for row in table.rows:
        #         for cell in row.cells:
        #             text_content += cell.text + " "
        #     text_content += "\n"
        #
        # if not text_content.strip():
        #     return None
        #
        # cleaned_text = self._clean_text(text_content)
        # language = self._detect_language(cleaned_text)
        # file_size = os.path.getsize(file_path)
        # doc_id = self._generate_doc_id(file_name)
        #
        # metadata = {
        #     "source": "docx",
        #     "file_size_bytes": file_size
        # }
        #
        # return Document(
        #     doc_id=doc_id,
        #     file_name=file_name,
        #     file_type='docx',
        #     content=cleaned_text,
        #     language=language,
        #     file_size=file_size,
        #     file_path=file_path,
        #     metadata=metadata
        # )
        return None

    def _process_txt(self, file_path: str, file_name: str) -> Optional[Document]:
        # with open(file_path, 'r', encoding='utf-8') as txt_file:
        #     text_content = txt_file.read()
        #
        # if not text_content.strip():
        #     return None
        #
        # cleaned_text = self._clean_text(text_content)
        # language = self._detect_language(cleaned_text)
        # file_size = os.path.getsize(file_path)
        # doc_id = self._generate_doc_id(file_name)
        #
        # metadata = {
        #     "source": "txt",
        #     "file_size_bytes": file_size
        # }
        #
        # return Document(
        #     doc_id=doc_id,
        #     file_name=file_name,
        #     file_type='txt',
        #     content=cleaned_text,
        #     language=language,
        #     file_size=file_size,
        #     file_path=file_path,
        #     metadata=metadata
        # )
        return None

    def _clean_text(self, text: str) -> str:
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')
        text = re.sub(r'\n\n\n+', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)
        text = text.strip()
        return text

    def _detect_language(self, text: str) -> str:
        try:
            if not text.strip():
                return 'unknown'

            sample_text = text[:5000] if len(text) > 5000 else text
            detected_lang = detect(sample_text)

            korean_count = len(re.findall(r'[\uac00-\ud7af]', text))
            english_count = len(re.findall(r'[a-zA-Z]', text))
            total_chars = len(re.findall(r'[\uac00-\ud7af]|[a-zA-Z]', text))

            if total_chars > 0:
                korean_ratio = korean_count / total_chars
                english_ratio = english_count / total_chars
                if korean_ratio > 0.05 and english_ratio > 0.05:
                    return 'mixed'

            if detected_lang == 'ko':
                return 'ko'
            elif detected_lang == 'en':
                return 'en'
            else:
                return detected_lang
        except:
            return 'unknown'

    def _generate_doc_id(self, file_name: str) -> str:
        timestamp = int(time.time() * 1000)
        hash_input = f"{file_name}_{timestamp}".encode('utf-8')
        hash_value = hashlib.md5(hash_input).hexdigest()[:12]
        file_base = Path(file_name).stem
        return f"{file_base}_{hash_value}"

    def _generate_metadata(self, documents: List[Document]) -> dict:
        """
        Generate metadata about processed documents.
        Returns:
            dict: Metadata including number of documents and language breakdown
        """
        total_docs = len(documents)

        language_counts = {
            'en': 0,
            'ko': 0,
            'mixed': 0,
            'unknown': 0
        }

        for doc in documents:
            if doc.language in language_counts:
                language_counts[doc.language] += 1
            else:
                language_counts['unknown'] += 1

        return {
            'total_documents': total_docs,
            'languages': language_counts
        }
