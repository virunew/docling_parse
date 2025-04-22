"""
Integration Tests for PDF Document Parsing

This module contains integration tests to verify that the document parsing 
functionality works correctly from end to end, including image extraction.
"""

import unittest
import os
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import test utilities for mock setup
from tests.test_utils import setup_mock_docling

# Add the src directory to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import necessary modules for testing
from src.parse_helper import process_pdf_document, save_output
from src.image_extraction_module import process_pdf_for_images


class TestDocumentParsingIntegration(unittest.TestCase):
    """Integration tests for the document parsing process."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary output directory
        self.output_dir = Path("tests/temp_output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock PDF path
        self.pdf_path = Path("tests/data/test.pdf")
        
        # Mock document data
        self.mock_document = MagicMock()
        self.mock_document.name = "test_document"
        
        # Create directory for the mocked document
        self.doc_output_dir = self.output_dir / "test_document"
        self.doc_output_dir.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary output directory
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
    
    @patch('src.parse_helper.convert_pdf_document')
    @patch('src.parse_helper.build_element_map')
    @patch('src.parse_helper.process_pdf_for_images')
    def test_process_pdf_document_with_images(self, mock_process_images, mock_build_element_map, mock_convert_pdf):
        """Test processing a PDF document with image extraction."""
        # Configure mocks
        mock_convert_pdf.return_value = self.mock_document
        
        # Mock element map
        mock_element_map = {
            "flattened_sequence": [
                {"id": "elem1", "type": "text", "content": "Test text"},
                {"id": "elem2", "type": "image", "content": ""}
            ],
            "elements": {
                "elem1": {"id": "elem1", "type": "text"},
                "elem2": {"id": "elem2", "type": "image"}
            }
        }
        mock_build_element_map.return_value = mock_element_map
        
        # Mock image processing
        mock_process_images.return_value = {
            "images": [
                {
                    "metadata": {
                        "id": "test_image_1",
                        "format": "image/png",
                        "file_path": f"{self.doc_output_dir}/images/test_image_1.png"
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
        result = process_pdf_document(self.pdf_path, self.output_dir)
        
        # Verify the results
        self.assertEqual(result, self.mock_document)
        
        # Verify that convert_pdf_document was called correctly
        mock_convert_pdf.assert_called_once()
        
        # Verify that build_element_map was called correctly
        mock_build_element_map.assert_called_once_with(self.mock_document)
        
        # Verify that process_pdf_for_images was called correctly
        mock_process_images.assert_called_once()
    
    @patch('src.parse_helper.convert_pdf_document')
    @patch('src.parse_helper.build_element_map')
    @patch('src.parse_helper.process_pdf_for_images')
    @patch('src.parse_helper.PDFImageExtractor')
    def test_process_pdf_document_with_fallback(self, mock_pdf_extractor_class, mock_process_images, 
                                              mock_build_element_map, mock_convert_pdf):
        """Test processing a PDF document with fallback to legacy image extraction."""
        # Configure mocks
        mock_convert_pdf.return_value = self.mock_document
        
        # Mock element map
        mock_element_map = {
            "flattened_sequence": [
                {"id": "elem1", "type": "text", "content": "Test text"},
                {"id": "elem2", "type": "image", "content": ""}
            ],
            "elements": {
                "elem1": {"id": "elem1", "type": "text"},
                "elem2": {"id": "elem2", "type": "image"}
            }
        }
        mock_build_element_map.return_value = mock_element_map
        
        # Mock process_pdf_for_images to raise an exception
        mock_process_images.side_effect = RuntimeError("Test error")
        
        # Mock legacy extractor
        mock_extractor = mock_pdf_extractor_class.return_value
        mock_extractor.extract_images.return_value = {
            "images": [
                {
                    "raw_data": b"test_image_data",
                    "metadata": {
                        "id": "test_image_1",
                        "format": "image/png"
                    }
                }
            ]
        }
        
        # Call the function
        result = process_pdf_document(self.pdf_path, self.output_dir)
        
        # Verify the results
        self.assertEqual(result, self.mock_document)
        
        # Verify that process_pdf_for_images was called
        mock_process_images.assert_called_once()
        
        # Verify that the fallback extractor was called
        mock_pdf_extractor_class.assert_called_once()
        mock_extractor.extract_images.assert_called_once_with(self.pdf_path)
    
    @patch('src.parse_helper.serialize_docling_document')
    def test_save_output(self, mock_serialize):
        """Test saving output to a file."""
        # Mock serialization result
        mock_serialize.return_value = {
            "name": "test_document",
            "content": "Test content"
        }
        
        # Create a mock images_data.json file
        images_data = {
            "images": [
                {
                    "metadata": {
                        "id": "test_image_1",
                        "format": "image/png"
                    }
                }
            ]
        }
        
        # Create directory structure
        doc_dir = self.output_dir / "test_document"
        doc_dir.mkdir(parents=True, exist_ok=True)
        
        # Write the mock images_data.json file
        with open(doc_dir / "images_data.json", "w") as f:
            json.dump(images_data, f)
        
        # Call the function
        result = save_output(self.mock_document, self.output_dir)
        
        # Verify the results
        expected_path = self.output_dir / "test_document.json"
        self.assertEqual(result, expected_path)
        self.assertTrue(expected_path.exists())
        
        # Verify that the output file contains the merged data
        with open(expected_path, "r") as f:
            data = json.load(f)
        
        self.assertEqual(data["name"], "test_document")
        self.assertEqual(data["content"], "Test content")
        self.assertIn("images_data", data)


if __name__ == "__main__":
    unittest.main() 