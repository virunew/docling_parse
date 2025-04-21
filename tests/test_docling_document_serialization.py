#!/usr/bin/env python3
"""
Integration tests for DoclingDocument serialization in parse_main.py

These tests verify that DoclingDocument objects are correctly serialized to JSON
when using the save_output function in parse_main.py.
"""

import os
import sys
import unittest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from save_output import save_output


class MockDoclingDocument:
    """Mock DoclingDocument class for testing."""
    
    def __init__(self, name="test_doc", pages=None):
        """Initialize a mock DoclingDocument with test data."""
        self.name = name
        self.pages = pages or []
        self.metadata = {"source": "test", "created": "2023-01-01"}
        
    def export_to_dict(self):
        """Mock the export_to_dict method."""
        return {
            "schema_name": "DoclingDocument",
            "version": "1.3.0",
            "name": self.name,
            "metadata": self.metadata,
            "pages": [
                {"id": f"page_{i+1}", "content": f"Page {i+1} content"} 
                for i in range(len(self.pages))
            ],
            "texts": [
                {"id": f"text_{i+1}", "content": f"Text {i+1} content"} 
                for i in range(3)
            ],
            "body": {
                "self_ref": "#/body",
                "children": [],
                "content_layer": "body",
                "name": "_root_",
                "label": "unspecified"
            },
            "furniture": {
                "self_ref": "#/furniture",
                "children": [],
                "content_layer": "furniture",
                "name": "_root_",
                "label": "unspecified"
            }
        }


class TestDoclingDocumentSerialization(unittest.TestCase):
    """Tests for DoclingDocument serialization functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary output directory
        self.output_dir = Path("test_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Create a mock document
        self.mock_doc = MockDoclingDocument(pages=[MagicMock() for _ in range(3)])
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove output file if it exists
        output_file = self.output_dir / "element_map.json"
        if output_file.exists():
            output_file.unlink()
        
        # Remove output directory if it exists
        if self.output_dir.exists():
            try:
                self.output_dir.rmdir()
            except OSError:
                # Directory not empty, which is fine for tests
                pass
    
    def test_save_output_creates_json_file(self):
        """Test that save_output creates a JSON file with the document data."""
        # Call the function under test
        save_output(self.mock_doc, self.output_dir)
        
        # Check that the output file was created
        output_file = self.output_dir / "element_map.json"
        self.assertTrue(output_file.exists(), "Output file was not created")
        
        # Check that the file contains valid JSON
        with open(output_file) as f:
            data = json.load(f)
        
        # Verify structure matches expected DoclingDocument format
        self.assertEqual(data["schema_name"], "DoclingDocument")
        self.assertEqual(data["version"], "1.3.0")
        self.assertEqual(data["name"], self.mock_doc.name)
        
        # Verify essential elements are present
        required_keys = ["body", "furniture", "texts"]
        for key in required_keys:
            self.assertIn(key, data, f"Missing required key: {key}")
    
    def test_save_output_directory_creation(self):
        """Test that save_output creates the output directory if it doesn't exist."""
        # Remove the directory if it exists
        import shutil
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        
        # Call the function under test
        save_output(self.mock_doc, self.output_dir)
        
        # Check that the directory was created
        self.assertTrue(self.output_dir.exists(), "Output directory was not created")
        
        # Check that the output file was created
        output_file = self.output_dir / "element_map.json"
        self.assertTrue(output_file.exists(), "Output file was not created")
    
    @patch('json.dump')
    def test_save_output_uses_document_export_method(self, mock_json_dump):
        """Test that save_output calls the document's export_to_dict method."""
        # Create a spy on the mock document's export_to_dict method
        mock_export = MagicMock(return_value={"test": "data"})
        self.mock_doc.export_to_dict = mock_export
        
        # Call the function under test
        save_output(self.mock_doc, self.output_dir)
        
        # Verify that export_to_dict was called
        mock_export.assert_called_once()
        
        # Verify that json.dump was called with the result of export_to_dict
        mock_json_dump.assert_called_once()
        args, _ = mock_json_dump.call_args
        self.assertEqual(args[0], {"test": "data"})


if __name__ == "__main__":
    unittest.main() 