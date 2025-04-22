"""
Unit tests for the enhanced image extraction module.
"""

import os
import json
import shutil
import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

import pytest

# Mock the docling imports before importing the module
sys.modules['docling.document_converter'] = MagicMock()
sys.modules['docling.datamodel.base_models'] = MagicMock()
sys.modules['docling.datamodel.pipeline_options'] = MagicMock()
sys.modules['docling.datamodel.document'] = MagicMock()

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the module to be tested
with patch('src.pdf_image_extractor.DocumentConverter'), \
     patch('src.pdf_image_extractor.InputFormat'), \
     patch('src.pdf_image_extractor.PdfFormatOption'), \
     patch('src.pdf_image_extractor.PdfPipelineOptions'), \
     patch('src.pdf_image_extractor.ConversionResult'):
    from src.image_extraction_module import (
        EnhancedImageExtractor,
        process_pdf_for_images
    )


class TestImageExtractionModule(unittest.TestCase):
    """
    Test cases for the enhanced image extraction module.
    """
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary test output directory
        self.test_output_dir = Path("test_output/image_extraction_test")
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a mock PDF path
        self.pdf_path = Path("test_data/sample.pdf")
        
        # Mock configuration
        self.config = {
            'images_scale': 2.0,
            'do_picture_description': True,
            'do_table_structure': True,
            'allow_external_plugins': True
        }
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the test output directory
        if self.test_output_dir.exists():
            shutil.rmtree(self.test_output_dir)
    
    @patch('src.image_extraction_module.PDFImageExtractor')
    def test_extract_and_save_images(self, mock_pdf_image_extractor):
        """Test the extract_and_save_images method."""
        # Create a mock for the PDFImageExtractor and its extract_images method
        mock_extractor_instance = MagicMock()
        mock_pdf_image_extractor.return_value = mock_extractor_instance
        
        # Create mock images data
        mock_images_data = {
            "document_name": "sample",
            "total_pages": 3,
            "images": [
                {
                    "metadata": {
                        "id": "picture_1",
                        "docling_ref": "#/pictures/0",
                        "page_number": 1,
                        "format": "image/png",
                        "size": {"width": 500, "height": 300}
                    },
                    "raw_data": b"mock_image_data_1"
                },
                {
                    "metadata": {
                        "id": "picture_2",
                        "docling_ref": "#/pictures/1",
                        "page_number": 2,
                        "format": "image/jpeg",
                        "size": {"width": 600, "height": 400}
                    },
                    "raw_data": b"mock_image_data_2"
                }
            ]
        }
        
        # Configure the mock to return our mock data
        mock_extractor_instance.extract_images.return_value = mock_images_data
        
        # Create a mock element map file
        element_map_data = {
            "flattened_sequence": [{"id": 1}, {"id": 2}],
            "elements": {"1": {}, "2": {}}
        }
        
        # Create the file-specific directory
        sample_dir = self.test_output_dir / "sample"
        sample_dir.mkdir(exist_ok=True)
        
        # Write the mock element map file
        with open(sample_dir / "element_map.json", "w") as f:
            json.dump(element_map_data, f)
        
        # Create an instance of EnhancedImageExtractor
        extractor = EnhancedImageExtractor(self.config)
        
        # Mock the relationship analyzer
        with patch('src.image_extraction_module.ImageContentRelationship') as mock_relationship:
            mock_relationship_instance = MagicMock()
            mock_relationship.return_value = mock_relationship_instance
            
            # Mock the analyze_relationships method
            enhanced_data = mock_images_data.copy()
            enhanced_data["enhanced"] = True
            mock_relationship_instance.analyze_relationships.return_value = enhanced_data
            
            # Call the method under test
            result = extractor.extract_and_save_images(self.pdf_path, self.test_output_dir)
            
            # Assertions
            mock_pdf_image_extractor.assert_called_once_with(self.config)
            mock_extractor_instance.extract_images.assert_called_once_with(self.pdf_path)
            
            # Check if the file-specific directory was created
            file_output_dir = self.test_output_dir / self.pdf_path.stem
            self.assertTrue(file_output_dir.exists())
            
            # Check if the images directory was created
            images_dir = file_output_dir / "images"
            self.assertTrue(images_dir.exists())
            
            # Check if images were saved
            self.assertTrue((images_dir / "picture_1.png").exists())
            self.assertTrue((images_dir / "picture_2.jpeg").exists())
            
            # Check if images_data.json was created
            images_data_path = file_output_dir / "images_data.json"
            self.assertTrue(images_data_path.exists())
            
            # Check the result
            self.assertEqual(result, enhanced_data)
    
    @patch('src.image_extraction_module.EnhancedImageExtractor')
    def test_process_pdf_for_images(self, mock_enhanced_extractor):
        """Test the process_pdf_for_images function."""
        # Create a mock for the EnhancedImageExtractor and its extract_and_save_images method
        mock_extractor_instance = MagicMock()
        mock_enhanced_extractor.return_value = mock_extractor_instance
        
        # Create mock images data
        mock_images_data = {"mock": "data"}
        
        # Configure the mock to return our mock data
        mock_extractor_instance.extract_and_save_images.return_value = mock_images_data
        
        # Call the function under test
        result = process_pdf_for_images(self.pdf_path, self.test_output_dir, self.config)
        
        # Assertions
        mock_enhanced_extractor.assert_called_once_with(self.config)
        mock_extractor_instance.extract_and_save_images.assert_called_once_with(
            self.pdf_path, self.test_output_dir
        )
        self.assertEqual(result, mock_images_data)
    
    @patch('src.image_extraction_module.PDFImageExtractor')
    def test_extract_images_error_handling(self, mock_pdf_image_extractor):
        """Test error handling in extract_and_save_images method."""
        # Create a mock for the PDFImageExtractor and configure it to raise an exception
        mock_extractor_instance = MagicMock()
        mock_pdf_image_extractor.return_value = mock_extractor_instance
        mock_extractor_instance.extract_images.side_effect = RuntimeError("Test error")
        
        # Create an instance of EnhancedImageExtractor
        extractor = EnhancedImageExtractor(self.config)
        
        # Test that the method raises a RuntimeError
        with self.assertRaises(RuntimeError):
            extractor.extract_and_save_images(self.pdf_path, self.test_output_dir)
    
    @patch('src.image_extraction_module.PDFImageExtractor')
    @patch('pathlib.Path.exists')
    def test_file_not_found_error(self, mock_exists, mock_pdf_image_extractor):
        """Test handling of non-existent PDF file."""
        # Configure Path.exists() to return False
        mock_exists.return_value = False
        
        # Create an instance of EnhancedImageExtractor
        extractor = EnhancedImageExtractor(self.config)
        
        # Test with a non-existent file
        non_existent_file = Path("test_data/non_existent.pdf")
        
        # Test that the method raises a FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            extractor.extract_and_save_images(non_existent_file, self.test_output_dir)


if __name__ == "__main__":
    unittest.main() 