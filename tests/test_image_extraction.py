#!/usr/bin/env python3
"""
Tests for image extraction and base64 data removal.

This module tests the functionality of extracting base64-encoded images and replacing
them with references to externally saved image files.
"""

import unittest
import os
import json
import shutil
import tempfile
from pathlib import Path
import base64

# Import the function to test
from src.json_metadata_fixer import fix_metadata, fix_image_references
from src.utils import replace_base64_with_file_references


class TestImageExtraction(unittest.TestCase):
    """Test cases for image extraction functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a sample base64 image
        self.sample_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        
        # Create sample document data with base64 image
        self.sample_document = {
            "pictures": [
                {
                    "data": f"data:image/png;base64,{self.sample_image_data}",
                    "width": 100,
                    "height": 100,
                }
            ],
            "element_map": {
                "pictures_0": {
                    "self_ref": "#/pictures/0",
                    "extracted_metadata": {
                        "metadata": {}
                    }
                }
            },
            "source_metadata": {
                "filename": "test_document.pdf"
            }
        }
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory and its contents
        shutil.rmtree(self.temp_dir)
    
    def test_image_extraction_replaces_base64(self):
        """Test that base64 image data is replaced with external file references."""
        # Run the fix_metadata function
        fixed_document = fix_metadata(self.sample_document, self.temp_dir)
        
        # Check if the pictures still have base64 data
        self.assertNotIn("data", fixed_document["pictures"][0], 
                         "Base64 image data should be removed")
        
        # Check if external_file references are added
        self.assertIn("external_file", fixed_document["pictures"][0],
                     "External file reference should be added")
        
        # Check if the image file is created
        images_dir = Path(self.temp_dir) / "images"
        image_files = list(images_dir.glob("*.*"))
        self.assertTrue(len(image_files) > 0, "Image file should be created")
        
        # Check if element map is updated with external_file reference
        self.assertIn("external_file", fixed_document["element_map"]["pictures_0"],
                     "Element map should be updated with external_file reference")
    
    def test_fix_image_references_function(self):
        """Test the fix_image_references function directly."""
        # Create images directory
        images_dir = Path(self.temp_dir) / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Run the fix_image_references function
        fixed_document = fix_image_references(self.sample_document, images_dir)
        
        # Check if the pictures still have base64 data
        self.assertNotIn("data", fixed_document["pictures"][0], 
                         "Base64 image data should be removed")
        
        # Check if external_file references are added
        self.assertIn("external_file", fixed_document["pictures"][0],
                     "External file reference should be added")
        
        # Check if the image file exists
        image_path = Path(fixed_document["pictures"][0]["external_file"])
        self.assertTrue((images_dir.parent / image_path).exists(), 
                        "Image file should exist at the specified path")
        
        # Check if the file contains the correct image data
        with open(images_dir.parent / image_path, "rb") as f:
            file_data = f.read()
        
        original_data = base64.b64decode(self.sample_image_data)
        self.assertEqual(file_data, original_data, 
                         "Saved image data should match the original")
    
    def test_integration_with_output_formatter(self):
        """Test integration with the output formatter."""
        from output_formatter import OutputFormatter
        
        # First fix the metadata
        fixed_document = fix_metadata(self.sample_document, self.temp_dir)
        
        # Create formatter with default config
        formatter = OutputFormatter()
        
        # Format as simplified JSON
        simplified_json = formatter.format_as_simplified_json(fixed_document)
        
        # Check if any images in the content reference base64 data
        for item in simplified_json.get("content", []):
            if item.get("type") == "image":
                self.assertNotIn("data:image/", item.get("url", ""), 
                                "Simplified JSON should not contain base64 image data")
        
        # Format as markdown
        markdown = formatter.format_as_markdown(fixed_document)
        self.assertNotIn("data:image/base64", markdown, 
                         "Markdown should not contain base64 image data")
        
        # Format as HTML
        html = formatter.format_as_html(fixed_document)
        self.assertNotIn("data:image/base64", html, 
                         "HTML should not contain base64 image data")

    def test_replace_base64_uri_field(self):
        """Test that base64 data in uri field is correctly replaced with file reference"""
        # Create test data with base64 image in uri field
        test_data = {
            "pictures": [
                {
                    "uri": f"data:image/png;base64,{self.sample_image_data}",
                    "id": "1"
                }
            ]
        }
        
        # Run the function under test
        result = replace_base64_with_file_references(test_data, self.temp_dir, "test_doc")
        
        # Check that the images directory was created
        images_dir = Path(self.temp_dir) / "test_doc" / "images"
        self.assertTrue(images_dir.exists())
        
        # Check that uri field was replaced with path reference
        self.assertFalse(result["pictures"][0]["uri"].startswith("data:image"))
        self.assertTrue(result["pictures"][0]["uri"].startswith("test_doc/images/"))
        self.assertTrue("external_file" in result["pictures"][0])
        
        # Check that the file was created and exists
        file_path = Path(self.temp_dir) / result["pictures"][0]["uri"]
        self.assertTrue(file_path.exists())
        
        # Verify file content
        with open(file_path, "rb") as f:
            file_data = f.read()
        self.assertEqual(file_data, base64.b64decode(self.sample_image_data))
    
    def test_replace_base64_data_uri_field(self):
        """Test that base64 data in data_uri field is correctly replaced with file reference"""
        # Create test data with base64 image in data_uri field
        test_data = {
            "pictures": [
                {
                    "data_uri": f"data:image/png;base64,{self.sample_image_data}",
                    "id": "2"
                }
            ]
        }
        
        # Run the function under test
        result = replace_base64_with_file_references(test_data, self.temp_dir, "test_doc")
        
        # Check that the images directory was created
        images_dir = Path(self.temp_dir) / "test_doc" / "images"
        self.assertTrue(images_dir.exists())
        
        # Check that data_uri field was replaced with path reference
        self.assertFalse(result["pictures"][0]["data_uri"].startswith("data:image"))
        self.assertTrue(result["pictures"][0]["data_uri"].startswith("test_doc/images/"))
        self.assertTrue("external_file" in result["pictures"][0])
        
        # Check that the file was created and exists
        file_path = Path(self.temp_dir) / result["pictures"][0]["data_uri"]
        self.assertTrue(file_path.exists())
        
        # Verify file content
        with open(file_path, "rb") as f:
            file_data = f.read()
        self.assertEqual(file_data, base64.b64decode(self.sample_image_data))
    
    def test_replace_base64_nested_structure(self):
        """Test that base64 data in deeply nested structure is correctly replaced"""
        # Create test data with deeply nested base64 image
        test_data = {
            "element_map": {
                "element1": {
                    "data": {
                        "image": {
                            "uri": f"data:image/png;base64,{self.sample_image_data}"
                        }
                    }
                }
            }
        }
        
        # Run the function under test
        result = replace_base64_with_file_references(test_data, self.temp_dir, "test_doc")
        
        # Check that the images directory was created
        images_dir = Path(self.temp_dir) / "test_doc" / "images"
        self.assertTrue(images_dir.exists())
        
        # Check that uri field was replaced with path reference
        uri = result["element_map"]["element1"]["data"]["image"]["uri"]
        self.assertFalse(uri.startswith("data:image"))
        self.assertTrue(uri.startswith("test_doc/images/"))
        
        # Check that the file was created and exists
        file_path = Path(self.temp_dir) / uri
        self.assertTrue(file_path.exists())


if __name__ == "__main__":
    unittest.main() 