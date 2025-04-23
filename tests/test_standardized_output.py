"""
Test module for standardized output functionality
"""
import json
import os
import unittest
import tempfile
from pathlib import Path

# Import the function to test
from format_standardized_output import create_standardized_output, save_standardized_output

class TestStandardizedOutput(unittest.TestCase):
    """Test cases for standardized output functionality"""
    
    def setUp(self):
        """Set up test case"""
        # Path to the sample JSON file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.sample_file = os.path.join(current_dir, "..", "output_main", "SBW_AI sample page10-11.json")
        self.output_dir = os.path.join(current_dir, "test_output")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load sample document data
        with open(self.sample_file, 'r', encoding='utf-8') as f:
            self.document_data = json.load(f)
    
    def test_create_standardized_output(self):
        """Test that the standardized output is created correctly"""
        # Sample document data
        document_data = {
            "pictures": [
                {
                    "id": "1",
                    "data_uri": "data:image/png;base64,abc123",
                    "page_number": 1
                }
            ],
            "texts": [
                {
                    "id": "2",
                    "text": "Sample text",
                    "page_number": 1
                }
            ]
        }

        # Create standardized output
        output = create_standardized_output(document_data)

        # Verify structure
        self.assertIn("chunks", output)
        self.assertIn("furniture", output)
        self.assertIn("source_metadata", output)

        # Verify chunks
        chunks = output["chunks"]
        self.assertGreater(len(chunks), 0)

        # Check if we have different types of chunks
        chunk_formats = set(chunk["format"] for chunk in chunks)
        print(f"Found chunk formats: {chunk_formats}")

        # In our sample, we should at least have image chunks
        self.assertIn("image", chunk_formats)

        # All chunks should have required fields
        for chunk in chunks:
            self.assertIn("format", chunk)
            self.assertIn("content", chunk)
            self.assertIn("metadata", chunk)

    def test_save_standardized_output(self):
        """Test that the standardized output is saved correctly"""
        # Sample document data
        document_data = {
            "pictures": [
                {
                    "id": "1",
                    "data_uri": "data:image/png;base64,abc123",
                    "page_number": 1
                }
            ]
        }

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save standardized output
            output_path = save_standardized_output(
                document_data, temp_dir, "test.pdf"
            )

            # Check that the file exists
            self.assertTrue(os.path.exists(output_path))

            # Verify the file content
            with open(output_path, "r", encoding="utf-8") as f:
                output = json.load(f)
                self.assertIn("chunks", output)
                self.assertIn("furniture", output)
                self.assertIn("source_metadata", output)

    def test_image_content_extraction(self):
        """Test that image content is correctly extracted"""
        # Sample document data with image
        document_data = {
            "pictures": [
                {
                    "id": "1",
                    "data_uri": "data:image/png;base64,abc123",
                    "page_number": 1,
                    "caption": "Sample image"
                }
            ]
        }

        # Create standardized output
        output = create_standardized_output(document_data)

        # Get image chunks
        image_chunks = [chunk for chunk in output["chunks"] if chunk["format"] == "image"]
        
        # Verify we have at least one image chunk
        self.assertTrue(len(image_chunks) > 0, "No image chunks found")
        
        # Verify image content is not empty
        for image_chunk in image_chunks:
            self.assertTrue(image_chunk["content"], "Image content is empty")
            # Verify image content format
            self.assertTrue(
                image_chunk["content"].startswith("data:image/"), 
                f"Invalid image content format: {image_chunk['content'][:30]}..."
            )
            
            # Verify metadata
            self.assertIn("caption", image_chunk["metadata"])

if __name__ == "__main__":
    unittest.main() 