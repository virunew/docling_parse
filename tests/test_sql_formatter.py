"""
Tests for the SQL Formatter module

This module tests the SQLFormatter class functionality to ensure it
correctly formats document data into SQL-compatible JSON format.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

from src.sql_formatter import SQLFormatter


class TestSQLFormatter(unittest.TestCase):
    """Test cases for the SQLFormatter class"""

    def setUp(self):
        """Set up test environment before each test"""
        self.formatter = SQLFormatter()
        
        # Create a temporary directory for output files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a sample document
        self.sample_document = {
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

    def tearDown(self):
        """Clean up after each test"""
        # Remove temporary directory and its contents
        shutil.rmtree(self.temp_dir)

    def test_format_as_sql_json(self):
        """Test the format_as_sql_json method"""
        # Call the method
        result = self.formatter.format_as_sql_json(self.sample_document)
        
        # Verify the structure
        self.assertIn("chunks", result)
        self.assertIn("furniture", result)
        self.assertIn("source", result)
        
        # Verify source metadata
        self.assertEqual(result["source"]["file_name"], "test_document.pdf")
        self.assertEqual(result["source"]["title"], "Test Document")
        self.assertEqual(result["source"]["author"], "Test Author")
        self.assertEqual(result["source"]["page_count"], 5)
        
        # Verify furniture
        self.assertEqual(result["furniture"]["title"], "Test Document")
        self.assertIn("This is the abstract", result["furniture"]["abstract"])
        
        # Verify chunks
        self.assertTrue(len(result["chunks"]) > 0)
        
        # Check specific chunk types
        text_chunks = [chunk for chunk in result["chunks"] if chunk["content_type"] == "text"]
        table_chunks = [chunk for chunk in result["chunks"] if chunk["content_type"] == "table"]
        image_chunks = [chunk for chunk in result["chunks"] if chunk["content_type"] == "image"]
        
        self.assertTrue(len(text_chunks) > 0)
        self.assertTrue(len(table_chunks) > 0)
        self.assertTrue(len(image_chunks) > 0)
        
        # Verify chunk content
        self.assertTrue(any("first paragraph" in chunk["content"] for chunk in text_chunks))
        self.assertTrue(any("Header 1" in chunk["content"] for chunk in table_chunks))
        self.assertTrue(any("image caption" in chunk["content"] for chunk in image_chunks))

    def test_save_formatted_output(self):
        """Test the save_formatted_output method"""
        # Call the method
        output_file = self.formatter.save_formatted_output(self.sample_document, self.temp_dir)
        
        # Verify the file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Load the saved file and verify contents
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertIn("chunks", saved_data)
        self.assertIn("furniture", saved_data)
        self.assertIn("source", saved_data)

    def test_empty_document(self):
        """Test handling of empty document"""
        with self.assertRaises(ValueError):
            self.formatter.format_as_sql_json({})

    def test_extract_source_metadata(self):
        """Test the _extract_source_metadata method"""
        metadata = self.formatter._extract_source_metadata(self.sample_document)
        
        self.assertEqual(metadata["file_name"], "test_document.pdf")
        self.assertEqual(metadata["title"], "Test Document")
        self.assertEqual(metadata["author"], "Test Author")
        self.assertEqual(metadata["page_count"], 5)
        self.assertEqual(metadata["content_type"], "document")

    def test_extract_furniture(self):
        """Test the _extract_furniture method"""
        furniture = self.formatter._extract_furniture(self.sample_document)
        
        self.assertEqual(furniture["title"], "Test Document")
        self.assertIn("abstract of the document", furniture["abstract"])
        self.assertIn("This is a footnote", furniture["footnotes"][0])

    def test_process_elements_to_chunks(self):
        """Test the _process_elements_to_chunks method"""
        chunks = self.formatter._process_elements_to_chunks(self.sample_document["elements"])
        
        self.assertTrue(len(chunks) >= 4)  # At least text, table, image, and more text chunks
        
        # Find chunks by content type
        text_chunks = [chunk for chunk in chunks if chunk["content_type"] == "text"]
        table_chunks = [chunk for chunk in chunks if chunk["content_type"] == "table"]
        image_chunks = [chunk for chunk in chunks if chunk["content_type"] == "image"]
        
        self.assertTrue(len(text_chunks) > 0)
        self.assertEqual(len(table_chunks), 1)
        self.assertEqual(len(image_chunks), 1)
        
        # Verify page ranges
        self.assertEqual(table_chunks[0]["page_range"], "2")
        self.assertEqual(image_chunks[0]["page_range"], "3")

    def test_generate_table_blocks(self):
        """Test the _generate_table_blocks method"""
        table_data = [
            ["Header 1", "Header 2", "Header 3"],
            ["Row 1, Cell 1", "Row 1, Cell 2", "Row 1, Cell 3"],
            ["Row 2, Cell 1", "Row 2, Cell 2", "Row 2, Cell 3"]
        ]
        
        table_text = self.formatter._generate_table_blocks(table_data)
        
        # Check table formatting
        self.assertIn("Header 1", table_text)
        self.assertIn("Row 1, Cell 1", table_text)
        self.assertIn("|", table_text)  # Check separator
        self.assertIn("-", table_text)  # Check header/data separator

    def test_format_image_text(self):
        """Test the _format_image_text method"""
        image_elem = {
            "type": "image",
            "caption": "Test caption",
            "ai_description": "AI description of image"
        }
        
        image_text = self.formatter._format_image_text(image_elem)
        
        self.assertIn("[IMAGE]", image_text)
        self.assertIn("Caption: Test caption", image_text)
        self.assertIn("Description: AI description", image_text)


if __name__ == '__main__':
    unittest.main() 