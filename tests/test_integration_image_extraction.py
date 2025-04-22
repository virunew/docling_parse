"""
Integration test for the image extraction module with parse_main.py.
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
sys.modules['docling'] = MagicMock()

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Create mock versions of needed functions and classes
with patch('src.parse_main.DocumentConverter'), \
     patch('src.parse_helper.DocumentConverter'), \
     patch('src.parse_main.InputFormat'), \
     patch('src.parse_helper.InputFormat'), \
     patch('src.parse_main.PdfFormatOption'), \
     patch('src.parse_helper.PdfFormatOption'), \
     patch('src.parse_main.PdfPipelineOptions'), \
     patch('src.parse_helper.PdfPipelineOptions'), \
     patch('src.pdf_image_extractor.DocumentConverter'), \
     patch('src.pdf_image_extractor.InputFormat'), \
     patch('src.pdf_image_extractor.PdfFormatOption'), \
     patch('src.pdf_image_extractor.PdfPipelineOptions'), \
     patch('src.pdf_image_extractor.ConversionResult'):

    # Module imports
    from src.parse_main import main
    from src.parse_helper import process_pdf_document
    from src.image_extraction_module import process_pdf_for_images


@pytest.mark.integration
class TestImageExtractionIntegration(unittest.TestCase):
    """
    Integration test cases for the image extraction module.
    """
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary test output directory
        self.test_output_dir = Path("test_output/integration_test")
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use a test PDF if available, otherwise use a mock path
        self.test_pdf = Path("test_data/sample.pdf")
        if not self.test_pdf.exists() and Path("test.pdf").exists():
            self.test_pdf = Path("test.pdf")  # Use test.pdf in the root directory if available
        
        # Create a mock DoclingDocument for testing
        self.mock_docling_document = MagicMock()
        self.mock_docling_document.name = "mock_document"
        self.mock_docling_document.pages = [MagicMock(), MagicMock()]
        
        # Mock element_map_builder to always return a valid element map
        patcher = patch('src.parse_helper.build_element_map', return_value={
            "flattened_sequence": [{"id": 1}, {"id": 2}],
            "elements": {"1": {}, "2": {}}
        })
        self.mock_build_element_map = patcher.start()
        self.addCleanup(patcher.stop)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the test output directory
        if self.test_output_dir.exists():
            shutil.rmtree(self.test_output_dir)
    
    @patch('src.parse_helper.DocumentConverter')
    @patch('src.parse_helper.process_pdf_for_images')
    def test_integration_with_process_pdf_document(self, mock_process_images, mock_doc_converter):
        """Test that process_pdf_document correctly uses the enhanced image extractor."""
        # Configure the DocumentConverter mock
        mock_converter_instance = MagicMock()
        mock_doc_converter.return_value = mock_converter_instance
        
        # Create a mock conversion result
        mock_conversion_result = MagicMock()
        mock_conversion_result.status = "success"
        mock_conversion_result.document = self.mock_docling_document
        
        # Configure the converter to return the mock result
        mock_converter_instance.convert.return_value = mock_conversion_result
        
        # Configure the process_pdf_for_images mock
        mock_process_images.return_value = {
            "document_name": "mock_document",
            "total_pages": 2,
            "images": [
                {
                    "metadata": {
                        "id": "picture_1",
                        "file_path": "images/picture_1.png"
                    }
                }
            ]
        }
        
        # Process the test PDF
        result = process_pdf_document(
            pdf_path=self.test_pdf,
            output_dir=self.test_output_dir
        )
        
        # Check that process_pdf_for_images was called with correct arguments
        mock_process_images.assert_called_once()
        call_args = mock_process_images.call_args[0]
        self.assertEqual(call_args[0], self.test_pdf)
        self.assertEqual(call_args[1], self.test_output_dir)
        
        # Check that the result is valid
        self.assertEqual(result, self.mock_docling_document)
    
    @patch('src.image_extraction_module.EnhancedImageExtractor')
    def test_direct_image_extraction(self, mock_enhanced_extractor):
        """Test direct use of the process_pdf_for_images function."""
        # Create a mock extractor instance
        mock_extractor_instance = MagicMock()
        mock_enhanced_extractor.return_value = mock_extractor_instance
        
        # Create mock image data
        mock_images_data = {
            "document_name": "sample",
            "total_pages": 2,
            "images": [
                {
                    "metadata": {
                        "id": "picture_1",
                        "file_path": "images/picture_1.png"
                    }
                }
            ]
        }
        
        # Configure the mock to return our test data
        mock_extractor_instance.extract_and_save_images.return_value = mock_images_data
        
        # Get the configuration
        config = {
            'images_scale': 2.0,
            'do_picture_description': True,
            'do_table_structure': True,
            'allow_external_plugins': True
        }
        
        # Process the test PDF directly
        images_data = process_pdf_for_images(
            pdf_path=self.test_pdf,
            output_dir=self.test_output_dir,
            config=config
        )
        
        # Check that the extractor was created with the correct config
        mock_enhanced_extractor.assert_called_once_with(config)
        
        # Check that extract_and_save_images was called with correct arguments
        mock_extractor_instance.extract_and_save_images.assert_called_once_with(
            self.test_pdf, self.test_output_dir
        )
        
        # Check that the result is valid
        self.assertEqual(images_data, mock_images_data)


if __name__ == "__main__":
    unittest.main() 