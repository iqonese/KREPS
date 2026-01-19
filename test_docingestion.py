import unittest
import os
from docingestion import DocumentIngestion, Document


class TestDocumentIngestion(unittest.TestCase):

    def setUp(self):
        """Run before each test"""
        self.ingestion = DocumentIngestion()

    def test_process_single_pdf(self):
        """Test processing a single PDF file"""
        file_paths = ["test_data/sample.pdf"]
        documents, metadata = self.ingestion.process_documents(file_paths)

        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].file_type, 'pdf')
        self.assertIsNotNone(documents[0].content)

    def test_language_detection_english(self):
        """Test English language detection"""
        text = "This is an English document with plenty of text."
        language = self.ingestion._detect_language(text)
        self.assertEqual(language, 'en')

    def test_language_detection_korean(self):
        """Test Korean language detection"""
        text = "이것은 한국어 문서입니다."
        language = self.ingestion._detect_language(text)
        self.assertEqual(language, 'ko')

    def test_language_detection_mixed(self):
        """Test mixed language detection"""
        text = "This is English text. 이것은 한국어입니다. More English here."
        language = self.ingestion._detect_language(text)
        self.assertEqual(language, 'mixed')

    def test_metadata_generation(self):
        """Test metadata counts"""
        documents = []
        metadata = self.ingestion._generate_metadata(documents)
        self.assertIn('total_documents', metadata)
        self.assertIn('languages', metadata)


if __name__ == '__main__':
    unittest.main()
