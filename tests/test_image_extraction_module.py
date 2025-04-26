"""
Test the enhanced image extraction module.

This module contains tests for the EnhancedImageExtractor class and its functionality.
"""

import unittest
import os
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import docling fix helper to fix imports
import docling_fix

# Mock the docling imports
sys.modules['docling.document_converter'] = MagicMock()
sys.modules['docling.datamodel.base_models'] = MagicMock()
sys.modules['docling.datamodel.pipeline_options'] = MagicMock()
sys.modules['docling_core.types.doc'] = MagicMock()

# Import the module to test
from src.image_extraction_module import EnhancedImageExtractor, process_pdf_for_images, retry_operation


class TestRetryOperation(unittest.TestCase):
    """Test cases for the retry_operation function."""
    
    def test_successful_operation(self):
        """Test that retry_operation returns the result for a successful operation."""
        mock_func = MagicMock(return_value="success")
        result = retry_operation(mock_func, args=(1, 2), kwargs={"key": "value"})
        self.assertEqual(result, "success")
        mock_func.assert_called_once_with(1, 2, key="value")
    
    def test_retry_then_success(self):
        """Test that retry_operation retries a failing operation until success."""
        mock_func = MagicMock(side_effect=[ValueError("Fail"), ValueError("Fail again"), "success"])
        result = retry_operation(
            mock_func, 
            max_retries=3, 
            delay=0.01,  # Use small delay for tests
            exceptions_to_retry=(ValueError,)
        )
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
    
    def test_all_retries_fail(self):
        """Test that retry_operation raises the last exception if all retries fail."""
        error = ValueError("All attempts failed")
        mock_func = MagicMock(side_effect=[ValueError("Fail"), ValueError("Fail again"), error])
        
        with self.assertRaises(ValueError) as context:
            retry_operation(
                mock_func, 
                max_retries=2, 
                delay=0.01,  # Use small delay for tests
                exceptions_to_retry=(ValueError,)
            )
        
        self.assertEqual(str(context.exception), "All attempts failed")
        self.assertEqual(mock_func.call_count, 3)  # Initial + 2 retries


class TestEnhancedImageExtractor(unittest.TestCase):
    """Test cases for the EnhancedImageExtractor class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary output directory
        self.output_dir = Path("tests/temp_output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock PDF path
        self.pdf_path = Path("tests/data/test.pdf")
        
        # Create a mock config
        self.config = {
            'images_scale': 2.0,
            'do_picture_description': True,
            'max_workers': 2,
            'max_retries': 2,
            'retry_delay': 0.01  # Small delay for tests
        }
        
        # Mock image data
        self.mock_image_data = {
            "images": [
                {
                    "raw_data": b"test_image_data",
                    "metadata": {
                        "id": "test_image_1",
                        "format": "image/png",
                        "page": 1,
                        "width": 100,
                        "height": 100
                    }
                }
            ],
            "metadata": {
                "file_path": str(self.pdf_path),
                "extraction_time": "2023-01-01T00:00:00"
            }
        }
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary output directory
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
    
    @patch('src.image_extraction_module.PDFImageExtractor')
    def test_extract_and_save_images(self, mock_extractor_class):
        """Test the extract_and_save_images method."""
        # Configure the mock
        mock_extractor = mock_extractor_class.return_value
        mock_extractor.extract_images.return_value = self.mock_image_data
        
        # Create the extractor
        extractor = EnhancedImageExtractor(self.config)
        
        # Create file-specific output directory (needed for image saving)
        file_output_dir = self.output_dir / self.pdf_path.stem
        file_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Call the method
        result = extractor.extract_and_save_images(self.pdf_path, self.output_dir)
        
        # Verify the results
        self.assertIn("images", result)
        self.assertIn("metadata", result)
        self.assertNotIn("relationships", result, "Relationships should not be added without element_map")
        
        # Verify that the image was saved
        images_dir = file_output_dir / "images"
        self.assertTrue(images_dir.exists())
        saved_image_files = list(images_dir.glob("*.png"))
        self.assertTrue(len(saved_image_files) > 0, "No image file was saved in the images directory")
        
        # Verify that extraction stats were recorded
        self.assertIn("extraction_stats", result)
        self.assertIn("successful", result["extraction_stats"])
    
    @patch('src.image_extraction_module.EnhancedImageExtractor')
    def test_process_pdf_for_images(self, mock_extractor_class):
        """Test the process_pdf_for_images function."""
        # Configure the mock
        mock_extractor = mock_extractor_class.return_value
        mock_extractor.extract_and_save_images.return_value = {
            "images": [
                {
                    "metadata": {
                        "id": "test_image_1",
                        "format": "image/png",
                        "file_path": "test/test_image_1.png"
                    }
                }
            ],
            "extraction_stats": {
                "successful": 1,
                "failed": 0,
                "retried": 0,
                "total_time": 0.5
            }
        }
        
        # Call the function
        result = process_pdf_for_images(self.pdf_path, self.output_dir, self.config)
        
        # Verify the results
        self.assertIn("images", result)
        self.assertEqual(len(result["images"]), 1)
        self.assertEqual(result["images"][0]["metadata"]["id"], "test_image_1")
        
        # Verify that the extractor was called with the correct arguments
        mock_extractor_class.assert_called_once_with(self.config)
        mock_extractor.extract_and_save_images.assert_called_once_with(
            self.pdf_path, self.output_dir
        )


if __name__ == "__main__":
    unittest.main() 