"""
SQL Formatter Tests

This module contains tests for the SQL formatter.
"""

import unittest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the SQLFormatter directly
from sql_formatter import SQLFormatter

class TestSQLFormatter(unittest.TestCase):
    """Unit tests for the SQL formatter."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Create a mock document for testing
        self.mock_document = {
            "pdf_name": "test_document.pdf",
            "pdf_info": {
                "Title": "Test Document",
                "Author": "Test Author",
                "Subject": "Test Subject",
                "Creator": "Test Creator",
                "Producer": "Test Producer",
                "CreationDate": "2023-01-01",
                "ModDate": "2023-01-02"
            },
            "num_pages": 5,
            "elements": [
                {
                    "type": "text",
                    "page_num": 1,
                    "text": "This is the title of the document",
                    "font_size": 16,
                    "y": 50,
                    "height": 20,
                    "page_height": 800
                },
                {
                    "type": "text",
                    "page_num": 1,
                    "text": "This is the abstract of the document which provides an overview.",
                    "font_size": 12,
                    "y": 100,
                    "height": 20,
                    "page_height": 800
                },
                {
                    "type": "text",
                    "page_num": 1,
                    "text": "This is the first paragraph of content.",
                    "font_size": 12,
                    "y": 150,
                    "height": 20,
                    "page_height": 800
                },
                {
                    "type": "table",
                    "page_num": 2,
                    "data": [
                        ["Header 1", "Header 2", "Header 3"],
                        ["Row 1, Cell 1", "Row 1, Cell 2", "Row 1, Cell 3"],
                        ["Row 2, Cell 1", "Row 2, Cell 2", "Row 2, Cell 3"]
                    ]
                },
                {
                    "type": "image",
                    "page_num": 3,
                    "image_index": 1,
                    "caption": "This is an image caption",
                    "ai_description": "This is an AI-generated description of the image"
                },
                {
                    "type": "text",
                    "page_num": 3,
                    "text": "This is content after the image.",
                    "font_size": 12,
                    "y": 300,
                    "height": 20,
                    "page_height": 800
                },
                {
                    "type": "text",
                    "page_num": 4,
                    "text": "This is a footnote.",
                    "font_size": 8,
                    "y": 750,
                    "height": 20,
                    "page_height": 800
                }
            ]
        }
        
        # Create SQLFormatter instance
        self.formatter = SQLFormatter()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_format_as_sql_json(self):
        """Test the basic SQL JSON formatting"""
        # Format the document
        formatted_data = self.formatter.format_as_sql_json(self.mock_document)
        
        # Verify basic structure
        self.assertIn("source", formatted_data)
        self.assertIn("furniture", formatted_data)
        self.assertIn("chunks", formatted_data)
        
        # Verify source information
        self.assertEqual(formatted_data["source"]["file_name"], "test_document.pdf")
        self.assertEqual(formatted_data["source"]["title"], "Test Document")
        self.assertEqual(formatted_data["source"]["author"], "Test Author")
        
        # Verify furniture contains metadata
        self.assertIn("title", formatted_data["furniture"])
        self.assertEqual(formatted_data["furniture"]["title"], "Test Document")
        
        # Verify chunks content
        chunks = formatted_data["chunks"]
        self.assertTrue(len(chunks) > 0)
    
    def test_save_formatted_output(self):
        """Test saving SQL-formatted output to a file"""
        # Format and save the document
        output_file = self.formatter.save_formatted_output(self.mock_document, str(self.output_dir))
        
        # Verify the file exists
        self.assertTrue(Path(output_file).exists())
        
        # Verify file extension
        self.assertTrue(output_file.endswith('.json'))
        
        # Check content
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        # Verify structure
        self.assertIn("source", saved_data)
        self.assertIn("furniture", saved_data)
        self.assertIn("chunks", saved_data)
    
    def test_extract_source_metadata(self):
        """Test the _extract_source_metadata method"""
        metadata = self.formatter._extract_source_metadata(self.mock_document)
        
        self.assertEqual(metadata["file_name"], "test_document.pdf")
        self.assertEqual(metadata["title"], "Test Document")
        self.assertEqual(metadata["author"], "Test Author")
        self.assertEqual(metadata["page_count"], 5)
        self.assertEqual(metadata["content_type"], "document")
    
    def test_extract_furniture(self):
        """Test the _extract_furniture method"""
        furniture = self.formatter._extract_furniture(self.mock_document)
        
        self.assertEqual(furniture["title"], "Test Document")
        self.assertIn("abstract of the document", furniture["abstract"])
        self.assertIn("This is a footnote", furniture["footnotes"][0])
    
    def test_empty_document(self):
        """Test handling of empty document"""
        with self.assertRaises(ValueError):
            self.formatter.format_as_sql_json({})

    @unittest.skip("Integration test requires actual parse_main module")
    @patch('src.parse_main.process_pdf_document')
    def test_integration_with_main(self, mock_process):
        """Test integration with main function using mock document"""
        # Skip this test for now as it requires more complex mocking
        pass


if __name__ == "__main__":
    unittest.main() 