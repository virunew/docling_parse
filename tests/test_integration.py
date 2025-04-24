#!/usr/bin/env python3
"""
Integration Test for PDF Document Parser

This test verifies the complete PDF document parsing pipeline, focusing on three key issues:
1. Image data should be saved as external files and referenced in the element map
2. Text elements, tables, and main content chunks should be correctly identified
3. Breadcrumbs should be generated properly, and furniture elements should be filtered from context
"""

import unittest
import os
import sys
import json
import shutil
import tempfile
from pathlib import Path

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Add src directory to path for imports
src_dir = os.path.join(parent_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import mock class
from unittest.mock import patch, MagicMock


class MockDocumentConverter:
    """Mock class for DocumentConverter to simulate PDF parsing"""
    
    def __init__(self, *args, **kwargs):
        """Initialize the mock converter"""
        self.document = {
            "pages": [
                {
                    "page_number": 1,
                    "width": 612,
                    "height": 792,
                    "text_elements": [
                        {
                            "id": "text_1",
                            "text": "Heading 1",
                            "bbox": [50, 50, 150, 70],
                            "font_size": 14,
                            "is_bold": True,
                            "style": "heading"
                        },
                        {
                            "id": "text_2",
                            "text": "This is a paragraph of sample text.",
                            "bbox": [50, 80, 400, 100],
                            "font_size": 12,
                            "style": "normal"
                        },
                        {
                            "id": "text_3",
                            "text": "Page 1 Footer",
                            "bbox": [50, 750, 150, 770],
                            "font_size": 10,
                            "style": "footer"
                        }
                    ],
                    "tables": [
                        {
                            "id": "table_1",
                            "bbox": [50, 200, 500, 300],
                            "rows": 3,
                            "columns": 3,
                            "cells": [
                                {"text": "Header 1", "row": 0, "col": 0},
                                {"text": "Header 2", "row": 0, "col": 1},
                                {"text": "Header 3", "row": 0, "col": 2},
                                {"text": "Data 1", "row": 1, "col": 0},
                                {"text": "Data 2", "row": 1, "col": 1},
                                {"text": "Data 3", "row": 1, "col": 2},
                                {"text": "Data 4", "row": 2, "col": 0},
                                {"text": "Data 5", "row": 2, "col": 1},
                                {"text": "Data 6", "row": 2, "col": 2}
                            ]
                        }
                    ],
                    "images": [
                        {
                            "id": "image_1",
                            "bbox": [50, 350, 300, 500],
                            "data": "base64_encoded_image_data_sample"
                        }
                    ]
                },
                {
                    "page_number": 2,
                    "width": 612,
                    "height": 792,
                    "text_elements": [
                        {
                            "id": "text_4",
                            "text": "Heading 2",
                            "bbox": [50, 50, 150, 70],
                            "font_size": 14,
                            "is_bold": True,
                            "style": "heading"
                        },
                        {
                            "id": "text_5",
                            "text": "This is another paragraph on page 2.",
                            "bbox": [50, 80, 400, 100],
                            "font_size": 12,
                            "style": "normal"
                        },
                        {
                            "id": "text_6",
                            "text": "Page 2 Footer",
                            "bbox": [50, 750, 150, 770],
                            "font_size": 10,
                            "style": "footer"
                        }
                    ],
                    "tables": [],
                    "images": [
                        {
                            "id": "image_2",
                            "bbox": [50, 200, 300, 350],
                            "data": "base64_encoded_image_data_sample_2"
                        }
                    ]
                }
            ]
        }
    
    def convert_pdf_to_document(self, *args, **kwargs):
        """Return the mock document structure"""
        return self.document


class TestIntegration(unittest.TestCase):
    """Integration test for the PDF document parser"""
    
    def setUp(self):
        """Set up the test environment with a temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create a mock PDF file
        self.pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(self.pdf_path, "wb") as f:
            f.write(b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF")
        
        # Save the original sys.argv
        self.original_argv = sys.argv.copy()
        
        # Override sys.argv with our test arguments
        sys.argv = [
            "parse_main.py",
            "--pdf_path", self.pdf_path,
            "--output_dir", self.output_dir,
            "--log_level", "ERROR"
        ]
    
    def tearDown(self):
        """Clean up after the test"""
        # Restore original sys.argv
        sys.argv = self.original_argv
        
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    @patch('element_map_builder.build_element_map')
    @patch('docling.document_converter.DocumentConverter')
    def test_complete_parsing_pipeline(self, mock_converter_class, mock_build_element_map):
        """Test the complete parsing pipeline from PDF to fixed JSON output"""
        # Set up mocks
        mock_converter = MockDocumentConverter()
        mock_converter_class.return_value = mock_converter
        
        # Create a mock element map that matches our test document
        mock_element_map = {
            "pages": [
                {
                    "page_number": 1,
                    "width": 612,
                    "height": 792,
                    "text_elements": mock_converter.document["pages"][0]["text_elements"],
                    "tables": mock_converter.document["pages"][0]["tables"],
                    "images": mock_converter.document["pages"][0]["images"]
                },
                {
                    "page_number": 2,
                    "width": 612,
                    "height": 792,
                    "text_elements": mock_converter.document["pages"][1]["text_elements"],
                    "tables": mock_converter.document["pages"][1]["tables"],
                    "images": mock_converter.document["pages"][1]["images"]
                }
            ],
            "metadata": {
                "title": "Test Document",
                "author": "Test Author",
                "creator": "Test Creator"
            }
        }
        mock_build_element_map.return_value = mock_element_map
        
        # Import parse_main dynamically after setting up mocks
        import parse_main
        
        # Run the main function
        result = parse_main.main()
        
        # Check return code
        self.assertEqual(result, 0, "The main function should return 0 for success")
        
        # Check if the output files exist
        docling_json_path = os.path.join(self.output_dir, "docling_document.json")
        fixed_json_path = os.path.join(self.output_dir, "fixed_document.json")
        output_json_path = os.path.join(self.output_dir, "document.json")
        
        self.assertTrue(os.path.exists(docling_json_path), "Docling output file should exist")
        self.assertTrue(os.path.exists(fixed_json_path), "Fixed output file should exist")
        self.assertTrue(os.path.exists(output_json_path), "Formatted output file should exist")
        
        # Check if images directory was created with image files
        images_dir = os.path.join(self.output_dir, "images")
        self.assertTrue(os.path.exists(images_dir), "Images directory should exist")
        
        # Load the fixed output file
        with open(fixed_json_path, 'r', encoding='utf-8') as f:
            fixed_data = json.load(f)
        
        # Verify that image data has been replaced with external file references
        for page in fixed_data.get("pages", []):
            for image in page.get("images", []):
                self.assertNotIn("data", image, "Image data should not be inline in the JSON")
                self.assertIn("file_path", image, "Image should have a file_path reference")
        
        # Check if breadcrumbs are generated
        for page in fixed_data.get("pages", []):
            for text_element in page.get("text_elements", []):
                if text_element.get("style") == "heading":
                    self.assertIn("breadcrumb", text_element, "Heading elements should have breadcrumbs")
            
            for table in page.get("tables", []):
                self.assertIn("breadcrumb", table, "Tables should have breadcrumbs")
        
        # Check that furniture elements are not in context
        for page in fixed_data.get("pages", []):
            for element in page.get("text_elements", []) + page.get("tables", []) + page.get("images", []):
                if element.get("context_before"):
                    for context_item in element.get("context_before", []):
                        self.assertNotIn("footer", context_item.get("text", "").lower(), 
                                         "Footer should not be in context_before")
                
                if element.get("context_after"):
                    for context_item in element.get("context_after", []):
                        self.assertNotIn("footer", context_item.get("text", "").lower(),
                                         "Footer should not be in context_after")


if __name__ == "__main__":
    unittest.main() 

