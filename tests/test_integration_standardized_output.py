"""
Integration test for standardized output generation

This test verifies that parse_main.py properly generates the standardized output
file with chunks and furniture arrays when processing a document.
"""

import os
import sys
import json
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test directly
from src.format_standardized_output import save_standardized_output

class TestStandardizedOutput(unittest.TestCase):
    """Test the standardized output generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Sample document data for testing
        self.document_data = {
            "name": "test_document",
            "element_map": {
                "flattened_sequence": [
                    {
                        "type": "text",
                        "text_content": "Sample text content",
                        "content_layer": "body"
                    },
                    {
                        "type": "text",
                        "text_content": "Header text",
                        "content_layer": "furniture"
                    }
                ]
            }
        }
    
    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_save_standardized_output_creates_required_structure(self):
        """Test that save_standardized_output creates the required output structure."""
        # Call the function directly
        output_file = save_standardized_output(
            self.document_data,
            self.temp_dir,
            "test.pdf"
        )
        
        # Check that the file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Load and check the contents
        with open(output_file, 'r') as f:
            output_data = json.load(f)
        
        # Check structure
        self.assertIn("chunks", output_data)
        self.assertIn("furniture", output_data)
        self.assertIn("source_metadata", output_data)
        
        # Check content
        self.assertEqual(len(output_data["chunks"]), 1)  # One content element
        self.assertEqual(len(output_data["furniture"]), 1)  # One furniture element
        self.assertEqual(output_data["furniture"][0], "Header text")
        
        # Check chunk fields match PRD requirements
        chunk = output_data["chunks"][0]
        required_fields = [
            "_id", "block_id", "doc_id", "content_type", "file_type", 
            "master_index", "coords_x", "coords_y", "coords_cx", "coords_cy",
            "author_or_speaker", "file_source", "table_block", "external_files",
            "text_block", "header_text", "text_search", "special_field1", 
            "special_field2", "creator_tool"
        ]
        
        for field in required_fields:
            self.assertIn(field, chunk, f"Required field '{field}' is missing from chunk")
        
        # Verify specific values
        self.assertEqual(chunk["creator_tool"], "DoclingToJsonScript_V1.1")
        self.assertEqual(chunk["content_type"], "text")
        self.assertEqual(chunk["block_id"], 1)

if __name__ == '__main__':
    unittest.main() 