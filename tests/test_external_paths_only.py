"""
Simplified test for external paths in standardized output
"""
import json
import sys
import os
import unittest

# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import only the format_standardized_output function
from format_standardized_output import create_standardized_output

class TestExternalPaths(unittest.TestCase):
    """Test external paths in standardized output"""
    
    def test_standardized_output_with_external_paths(self):
        """Test create_standardized_output function with external paths"""
        # Create sample document with external paths
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
        
        # Extract image chunks
        image_chunks = [chunk for chunk in output["chunks"] if chunk["format"] == "image"]
        
        # Verify there are 3 image chunks
        self.assertEqual(len(image_chunks), 3, "There should be exactly 3 image chunks")
        
        # Verify external paths were used correctly
        self.assertEqual(image_chunks[0]["content"], "images/image1.png")
        self.assertTrue(image_chunks[0]["metadata"]["is_external"])
        
        self.assertEqual(image_chunks[1]["content"], "images/image2.jpg")
        self.assertTrue(image_chunks[1]["metadata"]["is_external"])
        
        # External path should take precedence over data_uri
        self.assertEqual(image_chunks[2]["content"], "images/image3.gif")
        self.assertTrue(image_chunks[2]["metadata"]["is_external"])

if __name__ == "__main__":
    unittest.main() 