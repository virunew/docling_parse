"""
Test Utilities Module

This module provides utility functions and mock setup for testing the docling_parse components.
"""

import sys
from unittest.mock import MagicMock
from pathlib import Path
import os
import tempfile
import json
import shutil
import unittest
from unittest.mock import patch
import copy
import base64
import logging

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import docling fix helper
import docling_fix

# Add src directory to path
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import the module to test
from src.utils import remove_base64_data, replace_base64_with_file_references

# Set up test logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_mock_docling():
    """
    Creates mock functions and data for testing docling.
    
    Returns:
        tuple: (mock_process_func, mock_document_data, mock_sentences)
    """
    # Create mock document
    mock_document = MagicMock()
    
    # Set up metadata
    mock_document.metadata = {
        "title": "Test Document",
        "author": "Test Author",
        "date": "2023-01-01",
        "language": "en",
        "pages": 2
    }
    
    # Create pages
    page1 = MagicMock()
    page1.page_number = 1
    page1.width = 612
    page1.height = 792
    
    page2 = MagicMock()
    page2.page_number = 2
    page2.width = 612
    page2.height = 792
    
    # Create segments for page 1
    segment1 = MagicMock()
    segment1.id = "seg1"
    segment1.text = "This is the first segment."
    segment1.page_number = 1
    segment1.bbox = (10, 10, 200, 40)
    segment1.type = "text"
    
    segment2 = MagicMock()
    segment2.id = "seg2"
    segment2.text = "This is the second segment."
    segment2.page_number = 1
    segment2.bbox = (10, 50, 200, 80)
    segment2.type = "text"
    
    # Create segments for page 2
    segment3 = MagicMock()
    segment3.id = "seg3"
    segment3.text = "This is a segment on page 2."
    segment3.page_number = 2
    segment3.bbox = (10, 10, 200, 40)
    segment3.type = "text"
    
    # Create images
    image1 = MagicMock()
    image1.id = "img1"
    image1.page_number = 1
    image1.bbox = (250, 10, 450, 200)
    image1.caption = "Test Image 1"
    image1.path = "images/test_image1.png"
    
    # Create tables
    table1 = MagicMock()
    table1.id = "table1"
    table1.page_number = 2
    table1.bbox = (50, 100, 400, 300)
    table1.data = [["Header 1", "Header 2"], ["Data 1", "Data 2"]]
    table1.caption = "Test Table 1"
    
    # Assign segments and images to pages
    page1.segments = [segment1, segment2]
    page1.images = [image1]
    page1.tables = []
    
    page2.segments = [segment3]
    page2.images = []
    page2.tables = [table1]
    
    # Add pages to document
    mock_document.pages = [page1, page2]
    
    # Add sentences
    mock_document.sentences = [
        MagicMock(id="sent1", text="This is the first segment.", segments=["seg1"]),
        MagicMock(id="sent2", text="This is the second segment.", segments=["seg2"]),
        MagicMock(id="sent3", text="This is a segment on page 2.", segments=["seg3"])
    ]
    
    # Create mock processor
    mock_processor = MagicMock()
    mock_processor.process.return_value = mock_document
    
    return mock_document, mock_processor

def setup_temp_dir():
    """
    Creates a temporary directory for testing.
    
    Returns:
        str: Path to the temporary directory
    """
    return Path(tempfile.mkdtemp())

def cleanup_temp_dir(temp_dir):
    """
    Cleans up the temporary directory.
    
    Args:
        temp_dir: Path to the temporary directory
    """
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        
def write_mock_config(config_path, output_format="json", output_file=None):
    """
    Write a mock configuration file.
    
    Args:
        config_path: Path to write the configuration file
        output_format: Format for output
        output_file: Output file path
        
    Returns:
        str: Path to the configuration file
    """
    config = {
        "input": {
            "files": ["test.pdf"]
        },
        "output": {
            "format": output_format
        }
    }
    
    if output_file:
        config["output"]["file"] = output_file
        
    with open(config_path, 'w') as f:
        json.dump(config, f)
        
    return config_path

# Automatically set up the mocks when the module is imported
setup_mock_docling()

class TestUtils(unittest.TestCase):
    """Test suite for utility functions in utils.py"""
    
    def setUp(self):
        """Set up the test environment"""
        # Create test output directory
        self.test_dir = Path("tests/test_output")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Test document ID
        self.doc_id = "test_doc"
        
        # Test output location for images
        self.images_dir = self.test_dir / self.doc_id / "images"
        
        # Sample base64 encoded images for testing
        # Small 1x1 pixel images to keep the test data small
        self.png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        self.jpg_base64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigD//2Q=="
        
        # Test data structure with base64 content
        self.test_data = {
            "metadata": {
                "title": "Test Document",
                "author": "Test Author"
            },
            "pages": [
                {
                    "page_num": 1,
                    "elements": [
                        {
                            "type": "image",
                            "mime_type": "image/png",
                            "base64_data": self.png_base64,
                            "width": 100,
                            "height": 100
                        },
                        {
                            "type": "text",
                            "content": "This is a test text"
                        }
                    ]
                },
                {
                    "page_num": 2,
                    "elements": [
                        {
                            "type": "image",
                            "mime_type": "image/jpeg",
                            "base64_data": self.jpg_base64,
                            "width": 200,
                            "height": 200
                        },
                        {
                            "type": "text",
                            "content": "Another test text"
                        }
                    ]
                }
            ]
        }
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove test output directory if it exists
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_remove_base64_data(self):
        """Test the removal of base64 data from dictionaries and lists"""
        # Test dictionary with base64 data
        test_dict = {
            "type": "image",
            "base64_data": self.png_base64,
            "mime_type": "image/png"
        }
        
        # Make a copy to verify original is not modified
        test_dict_copy = test_dict.copy()
        
        # Test removing base64 from dictionary
        result = remove_base64_data(test_dict)
        
        # Verify the returned dictionary has base64 data removed
        self.assertEqual(result["base64_data"], "[BASE64_DATA_REMOVED]")
        
        # Original should remain unchanged
        self.assertEqual(test_dict, test_dict_copy)
        
        # Test list with base64 data
        test_list = ["normal text", f"data:image/png;base64,{self.png_base64}", "more text"]
        
        # Make a copy to verify original is not modified
        test_list_copy = test_list.copy()
        
        # Test removing base64 from list
        result = remove_base64_data(test_list)
        
        # Verify the returned list has base64 data removed
        self.assertEqual(result[1], "[BASE64_DATA_REMOVED]")
        
        # Original should remain unchanged
        self.assertEqual(test_list, test_list_copy)
    
    def test_replace_base64_with_file_references(self):
        """Test replacing base64 data with file references"""
        # Make a copy of test data to verify original not modified
        test_data_copy = self.test_data.copy()
        
        # Replace base64 data in test data
        result = replace_base64_with_file_references(
            self.test_data, 
            self.test_dir,
            self.doc_id
        )
        
        # Verify that images directory was created
        self.assertTrue(self.images_dir.exists())
        self.assertTrue(self.images_dir.is_dir())
        
        # Verify that image files were created (should be 2)
        image_files = list(self.images_dir.glob("*"))
        self.assertEqual(len(image_files), 2)
        
        # Check that base64 data was replaced with file references
        self.assertNotIn("base64_data", result["pages"][0]["elements"][0])
        self.assertIn("external_file", result["pages"][0]["elements"][0])
        self.assertNotIn("base64_data", result["pages"][1]["elements"][0])
        self.assertIn("external_file", result["pages"][1]["elements"][0])
        
        # Check that the paths are correct
        self.assertTrue(result["pages"][0]["elements"][0]["external_file"].startswith(f"{self.doc_id}/images/"))
        self.assertTrue(result["pages"][1]["elements"][0]["external_file"].startswith(f"{self.doc_id}/images/"))
        
        # Verify that non-image content remains unchanged
        self.assertEqual(result["pages"][0]["elements"][1]["content"], "This is a test text")
        self.assertEqual(result["pages"][1]["elements"][1]["content"], "Another test text")
        
        # Original data should not be modified
        self.assertEqual(self.test_data, test_data_copy)
        
        # Verify the image files were created with the correct content
        for page in result["pages"]:
            for element in page["elements"]:
                if element["type"] == "image" and "external_file" in element:
                    # Get the file path
                    file_path = self.test_dir / element["external_file"]
                    self.assertTrue(file_path.exists())
                    self.assertTrue(file_path.is_file())
                    
                    # Check that file is not empty
                    self.assertGreater(file_path.stat().st_size, 0)
    
    def test_replace_base64_with_file_references_error_handling(self):
        """Test error handling in replace_base64_with_file_references"""
        # Create test data with invalid base64
        invalid_data = {
            "type": "image",
            "mime_type": "image/png",
            "base64_data": "ThisIsNotValidBase64!!!"
        }
        
        # Replace should gracefully handle the error and return the original data
        result = replace_base64_with_file_references(
            invalid_data,
            self.test_dir,
            self.doc_id
        )
        
        # The result should contain the original base64 data
        self.assertEqual(result["base64_data"], "ThisIsNotValidBase64!!!")
    
if __name__ == "__main__":
    unittest.main() 