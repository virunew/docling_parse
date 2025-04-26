import unittest
import os
import sys
import copy
from pathlib import Path

# Add src directory to path
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import the common utils function
from src.utils import remove_base64_data


class TestBase64Removal(unittest.TestCase):
    """Test the base64 data removal functionality."""
    
    def setUp(self):
        """Set up test data with base64 content."""
        # Test data with various base64 patterns
        self.test_data = {
            "simple_string": "Normal text with data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
            "nested_dict": {
                "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA...",
                "normal_field": "Just text"
            },
            "list_with_images": [
                "data:image/jpg;base64,R0lGODlhAQABAIAAAAAAAP///yH5BA...",
                "No base64 here",
                {"another_image": "data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5..."}
            ],
            "deep_nested": {
                "level1": {
                    "level2": [
                        {"image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."}
                    ]
                }
            },
            "with_raw_data": {
                "raw_data": b"binary image data here"
            },
            "with_data_uri_key": {
                "image_data_uri": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
            }
        }
        
        # Expected result after base64 removal
        self.expected_result = {
            "simple_string": "Normal text with data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
            "nested_dict": {
                "image_data": "[BASE64_IMAGE_DATA_REMOVED]",
                "normal_field": "Just text"
            },
            "list_with_images": [
                "[BASE64_IMAGE_DATA_REMOVED]",
                "No base64 here",
                {"another_image": "[BASE64_IMAGE_DATA_REMOVED]"}
            ],
            "deep_nested": {
                "level1": {
                    "level2": [
                        {"image": "[BASE64_IMAGE_DATA_REMOVED]"}
                    ]
                }
            },
            "with_raw_data": {
                "raw_data": "[BINARY_IMAGE_DATA_REMOVED]"
            },
            "with_data_uri_key": {
                "image_data_uri": "[BASE64_IMAGE_DATA_REMOVED]"
            }
        }
        
    def test_remove_base64_data(self):
        """Test the base64 removal function."""
        # Create a copy to ensure the original is not modified
        test_copy = copy.deepcopy(self.test_data)
        
        # Apply the function
        result = remove_base64_data(test_copy)
        
        # Assert the result matches the expected output
        self.assertEqual(result, self.expected_result)
        
        # Assert that the original data remains unchanged by the function
        self.assertIn("data:image/png;base64,", self.test_data["simple_string"])
    
    def test_nested_dict_base64_removal(self):
        """Test removing base64 from a nested dictionary."""
        nested_dict = self.test_data["nested_dict"]
        result = remove_base64_data(nested_dict)
        
        self.assertEqual(result["image_data"], "[BASE64_IMAGE_DATA_REMOVED]")
        self.assertEqual(result["normal_field"], "Just text")
    
    def test_list_base64_removal(self):
        """Test removing base64 from a list with mixed content."""
        list_data = self.test_data["list_with_images"]
        result = remove_base64_data(list_data)
        
        self.assertEqual(result[0], "[BASE64_IMAGE_DATA_REMOVED]")
        self.assertEqual(result[1], "No base64 here")  # Regular text should be unchanged
        self.assertEqual(result[2]["another_image"], "[BASE64_IMAGE_DATA_REMOVED]")
    
    def test_deep_nested_base64_removal(self):
        """Test removing base64 from deeply nested structures."""
        deep_nested = self.test_data["deep_nested"]
        result = remove_base64_data(deep_nested)
        
        self.assertEqual(
            result["level1"]["level2"][0]["image"], 
            "[BASE64_IMAGE_DATA_REMOVED]"
        )
    
    def test_binary_data_removal(self):
        """Test removing binary raw_data."""
        with_raw_data = self.test_data["with_raw_data"]
        result = remove_base64_data(with_raw_data)
        
        self.assertEqual(result["raw_data"], "[BINARY_IMAGE_DATA_REMOVED]")
    
    def test_data_uri_key_removal(self):
        """Test removing base64 from keys containing 'data_uri'."""
        with_data_uri_key = self.test_data["with_data_uri_key"]
        result = remove_base64_data(with_data_uri_key)
        
        self.assertEqual(result["image_data_uri"], "[BASE64_IMAGE_DATA_REMOVED]")


if __name__ == "__main__":
    unittest.main() 