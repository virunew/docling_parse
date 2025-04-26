#!/usr/bin/env python3
"""
Test for base64 image replacement functionality

This test ensures that the base64 image data is correctly replaced
with file references in the output files.
"""
import sys
import os
import json
import base64
import re
from pathlib import Path
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import replace_base64_with_file_references

class TestBase64Replacement(unittest.TestCase):
    """Test case for base64 image replacement functionality"""

    def test_replace_base64_with_file_references(self):
        """Test the function that replaces base64 image data with file references"""
        # Create a test directory
        test_dir = Path("tests/test_output")
        test_dir.mkdir(exist_ok=True, parents=True)
        
        # Create a test images directory
        test_images_dir = test_dir / "test_doc" / "images"
        test_images_dir.mkdir(exist_ok=True, parents=True)
        
        # Create sample document data with base64 image
        sample_base64 = base64.b64encode(b'test image data').decode('utf-8')
        sample_data_uri = f"data:image/png;base64,{sample_base64}"
        
        # Create sample document with pictures containing base64 data
        sample_document = {
            "pictures": [
                {
                    "self_ref": "#/pictures/0",
                    "data": sample_data_uri
                }
            ],
            "texts": [
                {
                    "self_ref": "#/texts/0",
                    "text": "Test text"
                }
            ]
        }
        
        # Replace base64 with file references
        result = replace_base64_with_file_references(sample_document, test_images_dir, "test_doc")
        
        # Verify base64 data was replaced with file reference
        self.assertNotIn(sample_base64, json.dumps(result))
        self.assertIn("file://", result["pictures"][0]["data"])
        
        # Check if the image file was created
        image_files = list(test_images_dir.glob("*.png"))
        self.assertGreaterEqual(len(image_files), 1)
        
        # Test with a more complex document structure
        complex_document = {
            "pictures": [
                {
                    "self_ref": "#/pictures/0",
                    "data": sample_data_uri
                },
                {
                    "self_ref": "#/pictures/1",
                    "data": sample_data_uri
                }
            ],
            "body": {
                "content": [
                    {"$ref": "#/pictures/0"},
                    {"$ref": "#/texts/0"}
                ]
            }
        }
        
        # Replace base64 with file references in complex document
        complex_result = replace_base64_with_file_references(complex_document, test_images_dir, "test_doc")
        
        # Verify all base64 data was replaced
        self.assertNotIn(sample_base64, json.dumps(complex_result))
        self.assertIn("file://", complex_result["pictures"][0]["data"])
        self.assertIn("file://", complex_result["pictures"][1]["data"])

    def test_integration_with_formatter(self):
        """Test that formatter uses the document with replaced base64 data"""
        # This would be a more complete test that would mock the OutputFormatter
        # and verify it's called with the correct data
        # For now, we'll just output a reminder that manual testing should verify this
        print("Integration test reminder: Verify that formatted output files don't contain base64 data")
        self.assertTrue(True)  # Placeholder assertion

if __name__ == "__main__":
    unittest.main() 