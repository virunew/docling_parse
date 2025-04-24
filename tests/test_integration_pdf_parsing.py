"""
Integration Test for PDF Parsing Pipeline

This test verifies that the entire PDF parsing pipeline works correctly
with the fixes to element_map_builder.py for handling TextItem objects.
"""

import sys
import os
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import json
import tempfile
import shutil

# Add parent directory to sys.path to find src modules
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
# Disable logging for tests
logging.disable(logging.CRITICAL)

# Import modules to test
from src.parse_helper import process_pdf_document
from src.element_map_builder import build_element_map


class TestPDFParsingIntegration(unittest.TestCase):
    """
    Integration tests for the PDF parsing pipeline.
    
    These tests use mocking to simulate the PDF processing workflow
    without requiring actual PDF files.
    """
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for test output
        self.test_output_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after tests"""
        # Remove the temporary directory
        shutil.rmtree(self.test_output_dir)
    
    @patch('src.parse_helper.convert_pdf_document')
    def test_element_map_building_with_text_items(self, mock_convert_pdf):
        """Test that the element map builder correctly handles TextItem objects"""
        # Create a mock document with TextItem-like objects
        mock_doc = MagicMock()
        mock_doc.name = "test_doc"
        
        # Create text items using a class that simulates Pydantic objects
        class TextItem:
            def __init__(self, self_ref, text="Sample text"):
                self.self_ref = self_ref
                self.text = text
                # Other attributes a real TextItem might have
                self.label = "text"
                self.content_layer = "body"
        
        # Create a sample document structure
        text1 = TextItem("#/texts/0", "First text item")
        text2 = TextItem("#/texts/1", "Second text item")
        mock_doc.texts = [text1, text2]
        mock_doc.tables = []
        mock_doc.pictures = []
        mock_doc.groups = []
        mock_doc.pages = [MagicMock()]  # One page
        
        # Create body structure
        body = MagicMock()
        body.elements = ["#/texts/0", "#/texts/1"]
        mock_doc.body = body
        
        # Set up the mock to return our document
        mock_convert_pdf.return_value = mock_doc
        
        # Mock path to a fake PDF
        mock_pdf_path = "/fake/path/to/test.pdf"
        
        try:
            # Process the mock PDF document
            with patch('src.parse_helper.build_element_map') as mock_build_map:
                # Call the real build_element_map function instead of the mock
                mock_build_map.side_effect = build_element_map
                
                # Process the document
                process_pdf_document(mock_pdf_path, self.test_output_dir)
                
                # Verify build_element_map was called with the right document
                mock_build_map.assert_called_once()
                
                # Extract the document that was passed to build_element_map
                called_doc = mock_build_map.call_args[0][0]
                
                # Verify document has the expected structure
                self.assertEqual(called_doc.name, "test_doc")
                
                # Test the actual build_element_map function directly
                element_map = build_element_map(mock_doc)
                
                # Verify the element map was created correctly
                self.assertIn("elements", element_map)
                self.assertIn("flattened_sequence", element_map)
                self.assertEqual(len(element_map["elements"]), 2)
                self.assertEqual(len(element_map["flattened_sequence"]), 2)
                
                # Check that elements were properly converted
                self.assertIn("#/texts/0", element_map["elements"])
                self.assertIn("#/texts/1", element_map["elements"])
                
        except Exception as e:
            self.fail(f"Test failed with exception: {e}")


if __name__ == "__main__":
    unittest.main() 