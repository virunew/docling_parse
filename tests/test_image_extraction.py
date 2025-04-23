#!/usr/bin/env python3
"""
Test module for verifying image content extraction
"""
import json
import os
import unittest
from pathlib import Path

# Import the function to test
from format_standardized_output import create_standardized_output

class TestImageExtraction(unittest.TestCase):
    """Test cases for image content extraction"""
    
    def setUp(self):
        """Set up test case"""
        # Current directory is the test directory
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        # Path to the sample JSON file
        self.sample_file = os.path.join(self.current_dir, "..", "output_main", "SBW_AI sample page10-11.json")
        
        # Load sample document data
        with open(self.sample_file, 'r', encoding='utf-8') as f:
            self.document_data = json.load(f)
    
    def test_image_data_extraction(self):
        """Test that the image data is correctly extracted from the input"""
        # Create standardized output
        output = create_standardized_output(self.document_data)
        
        # Check if there are image chunks
        image_chunks = [chunk for chunk in output["chunks"] if chunk["format"] == "image"]
        self.assertGreater(len(image_chunks), 0, "There should be at least one image chunk")
        
        # Check that image content is not empty
        for chunk in image_chunks:
            self.assertNotEqual(chunk["content"], "", "Image content should not be empty")
            self.assertTrue(chunk["content"].startswith("data:image"), 
                           f"Image content should start with 'data:image', got: {chunk['content'][:20]}...")
    
    def test_sample_document_with_different_formats(self):
        """Test the formatting of a document with different image formats"""
        # Create a sample document with different image formats
        sample_doc = {
            "pictures": [
                {
                    "id": "1",
                    "data_uri": "data:image/png;base64,abc123",
                    "page_number": 1
                },
                {
                    "id": "2",
                    "image": {
                        "uri": "data:image/jpeg;base64,def456",
                        "mimetype": "image/jpeg"
                    },
                    "page_number": 2
                },
                {
                    "id": "3",
                    "image": {
                        "mimetype": "image/gif",
                        "data": "ghi789"
                    },
                    "page_number": 3
                }
            ]
        }
        
        # Create standardized output
        output = create_standardized_output(sample_doc)
        
        # Check if there are exactly 3 image chunks
        image_chunks = [chunk for chunk in output["chunks"] if chunk["format"] == "image"]
        self.assertEqual(len(image_chunks), 3, "There should be exactly 3 image chunks")
        
        # Verify each chunk has the correct content
        self.assertEqual(image_chunks[0]["content"], "data:image/png;base64,abc123")
        self.assertEqual(image_chunks[1]["content"], "data:image/jpeg;base64,def456")
        self.assertEqual(image_chunks[2]["content"], "data:image/gif;base64,ghi789")

    def test_external_file_paths(self):
        """Test handling of external file paths for images"""
        # Create a sample document with external image paths
        sample_doc = {
            "pictures": [
                {
                    "id": "1",
                    "external_path": "images/image1.png",
                    "page_number": 1
                },
                {
                    "id": "2",
                    "metadata": {
                        "file_path": "images/image2.jpg"
                    },
                    "page_number": 2
                },
                # Mixed case - has both data_uri and external_path (external_path should be prioritized)
                {
                    "id": "3",
                    "external_path": "images/image3.gif",
                    "data_uri": "data:image/gif;base64,test123",
                    "page_number": 3
                }
            ]
        }
        
        # Create standardized output
        output = create_standardized_output(sample_doc)
        
        # Check if there are exactly 3 image chunks
        image_chunks = [chunk for chunk in output["chunks"] if chunk["format"] == "image"]
        self.assertEqual(len(image_chunks), 3, "There should be exactly 3 image chunks")
        
        # Verify each chunk has the correct content
        self.assertEqual(image_chunks[0]["content"], "images/image1.png")
        self.assertEqual(image_chunks[0]["metadata"]["is_external"], True)
        
        self.assertEqual(image_chunks[1]["content"], "images/image2.jpg")
        self.assertEqual(image_chunks[1]["metadata"]["is_external"], True)
        
        # Test that external_path takes precedence over data_uri
        self.assertEqual(image_chunks[2]["content"], "images/image3.gif")
        self.assertEqual(image_chunks[2]["metadata"]["is_external"], True)

if __name__ == "__main__":
    unittest.main() 