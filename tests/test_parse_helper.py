"""
Tests for parse_helper.py

This module contains tests for the parse_helper.py module, which provides
high-level functions for processing PDF documents using the docling library.
"""

import os
import sys
import json
import pytest
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import base64

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock docling imports
sys.modules['docling_fix'] = MagicMock()
sys.modules['docling'] = MagicMock()
sys.modules['docling.document_converter'] = MagicMock()
sys.modules['docling.datamodel'] = MagicMock()
sys.modules['docling.datamodel.base_models'] = MagicMock()
sys.modules['docling.datamodel.pipeline_options'] = MagicMock()
sys.modules['docling.datamodel.document'] = MagicMock()
sys.modules['docling.document_converter.DocumentConverter'] = MagicMock()
sys.modules['docling.datamodel.base_models.InputFormat'] = MagicMock()
sys.modules['docling.document_converter.PdfFormatOption'] = MagicMock()
sys.modules['docling.datamodel.pipeline_options.PdfPipelineOptions'] = MagicMock()
sys.modules['docling.datamodel.document.ConversionResult'] = MagicMock()
sys.modules['docling_core.types.doc'] = MagicMock()
sys.modules['docling_core.types.doc.DoclingDocument'] = MagicMock()

# Mock other modules that depend on docling
sys.modules['element_map_builder'] = MagicMock()
sys.modules['pdf_image_extractor'] = MagicMock()
sys.modules['image_extraction_module'] = MagicMock()
sys.modules['metadata_extractor'] = MagicMock()
sys.modules['logger_config'] = MagicMock()
sys.modules['docling_integration'] = MagicMock()

# Now import parse_helper after mocking its dependencies
from src.parse_helper import process_pdf_document, save_output, process_extracted_images


class TestParseHelper:
    """Test suite for parse_helper.py module."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Create a temporary PDF file
        self.pdf_path = Path(self.temp_dir.name) / "test.pdf"
        self.pdf_path.touch()  # Create empty file
        
        # Create a temporary config file
        self.config_path = Path(self.temp_dir.name) / "config.json"
        with open(self.config_path, 'w') as f:
            json.dump({
                "pdf_pipeline_options": {
                    "images_scale": 3.0,
                    "do_table_structure": False
                }
            }, f)
        
        # Create a mock DoclingDocument
        self.mock_document = MagicMock()
        self.mock_document.name = "test_document"
        self.mock_document.pages = [MagicMock(), MagicMock()]
        
        # Set up mocks for imported modules
        from src.docling_integration import convert_pdf_document, create_pdf_pipeline_options
        convert_pdf_document.return_value = self.mock_document
        
        from src.element_map_builder import build_element_map
        self.mock_element_map = {
            "elements": {
                "page_1": {"id": "page_1", "metadata": {"type": "page"}},
                "page_1_paragraph_1": {"id": "page_1_paragraph_1", "metadata": {"type": "paragraph"}}
            },
            "flattened_sequence": [
                {"id": "page_1", "metadata": {"type": "page"}},
                {"id": "page_1_paragraph_1", "metadata": {"type": "paragraph"}}
            ]
        }
        build_element_map.return_value = self.mock_element_map
        
        from src.metadata_extractor import extract_full_metadata
        extract_full_metadata.return_value = {"breadcrumb": "page_1/paragraph_1"}
        
        from src.image_extraction_module import process_pdf_for_images
        process_pdf_for_images.return_value = {
            "document_name": "test_document",
            "total_pages": 2,
            "images": [
                {
                    "metadata": {
                        "id": "image_1",
                        "docling_ref": "#/pictures/0",
                        "page_number": 1
                    }
                }
            ]
        }
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    @patch('src.docling_integration.convert_pdf_document')
    @patch('src.element_map_builder.build_element_map')
    @patch('src.docling_integration.create_pdf_pipeline_options')
    @patch('src.image_extraction_module.process_pdf_for_images')
    @patch('src.metadata_extractor.extract_full_metadata')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    def test_process_pdf_document(self, mock_mkdir, mock_file, mock_extract_metadata, 
                                 mock_process_images, mock_create_options, 
                                 mock_build_map, mock_convert_pdf):
        """Test the PDF document processing workflow."""
        # Set up mocks
        mock_convert_pdf.return_value = self.mock_document
        mock_build_map.return_value = self.mock_element_map
        mock_extract_metadata.return_value = {"breadcrumb": "page_1/paragraph_1"}
        mock_process_images.return_value = {
            "document_name": "test_document",
            "total_pages": 2,
            "images": []
        }
        
        # Call the function
        result = process_pdf_document(self.pdf_path, self.output_dir, self.config_path)
        
        # Verify results
        assert result is self.mock_document
        mock_mkdir.assert_called()  # Check that directories were created
        mock_convert_pdf.assert_called_once()
        mock_build_map.assert_called_once_with(self.mock_document)
        
        # Check that element map was saved
        assert mock_file.call_count >= 2
        
        # Verify extraction of metadata and images
        mock_extract_metadata.assert_called()
        mock_process_images.assert_called_once_with(self.pdf_path, self.output_dir, {
            'images_scale': 2.0,
            'do_picture_description': True,
            'do_table_structure': True,
            'allow_external_plugins': True
        })
    
    @patch('src.docling_integration.convert_pdf_document')
    @patch('src.image_extraction_module.process_pdf_for_images')
    @patch('src.pdf_image_extractor.PDFImageExtractor')
    def test_process_pdf_document_fallback_image_extraction(self, mock_image_extractor_class, 
                                                           mock_process_images, mock_convert_pdf):
        """Test fallback to legacy image extraction when enhanced extraction fails."""
        # Set up mocks
        mock_convert_pdf.return_value = self.mock_document
        
        # Mock enhanced image extraction to fail
        mock_process_images.side_effect = Exception("Enhanced extraction failed")
        
        # Mock legacy image extraction
        mock_image_extractor = MagicMock()
        mock_image_extractor_class.return_value = mock_image_extractor
        mock_image_extractor.extract_images.return_value = {
            "document_name": "test_document",
            "total_pages": 2,
            "images": [
                {
                    "metadata": {
                        "id": "image_1"
                    },
                    "raw_data": b"test image data"
                }
            ]
        }
        
        # Call the function
        result = process_pdf_document(self.pdf_path, self.output_dir)
        
        # Verify results
        assert result is self.mock_document
        mock_process_images.assert_called_once()
        mock_image_extractor_class.assert_called_once()
        mock_image_extractor.extract_images.assert_called_once_with(self.pdf_path)
    
    @patch('src.docling_integration.serialize_docling_document')
    @patch('src.docling_integration.merge_with_image_data')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_save_output(self, mock_exists, mock_file, mock_merge, mock_serialize):
        """Test saving document output."""
        # Set up mocks
        mock_serialize.return_value = {
            "name": "test_document",
            "pages": [{"id": "page_1"}, {"id": "page_2"}]
        }
        
        mock_exists.return_value = True
        
        mock_merge.return_value = {
            "name": "test_document",
            "pages": [{"id": "page_1"}, {"id": "page_2"}],
            "images_data": {"images": []}
        }
        
        # Call the function
        result = save_output(self.mock_document, self.output_dir)
        
        # Verify results
        assert result == self.output_dir / "test_document.json"
        mock_serialize.assert_called_once_with(self.mock_document)
        mock_merge.assert_called_once()
        assert mock_file.call_count >= 1
    
    @patch('builtins.open', new_callable=mock_open)
    def test_process_extracted_images(self, mock_file):
        """Test processing extracted images."""
        # Create test data
        images_data = {
            "images": [
                {
                    "metadata": {
                        "id": "image_1",
                        "format": "image/png"
                    },
                    "raw_data": b"test image data"
                },
                {
                    "metadata": {
                        "id": "image_2",
                        "format": "image/jpeg"
                    },
                    "raw_data": b"another test image"
                }
            ]
        }
        
        images_dir = Path(self.temp_dir.name) / "images"
        output_path = Path(self.temp_dir.name)
        
        # Call the function
        process_extracted_images(images_data, images_dir, output_path)
        
        # Verify results
        assert mock_file.call_count == 2
        
        # Check that raw_data was removed
        for image in images_data["images"]:
            assert "raw_data" not in image
            assert "file_path" in image["metadata"]
    
    @patch('src.docling_integration.convert_pdf_document')
    def test_process_pdf_document_error_handling(self, mock_convert_pdf):
        """Test error handling in process_pdf_document."""
        # Set up mock to raise an exception
        mock_convert_pdf.side_effect = RuntimeError("Conversion failed")
        
        # Call the function and expect an exception
        with pytest.raises(Exception) as excinfo:
            process_pdf_document(self.pdf_path, self.output_dir)
        
        # Verify error message
        assert "Error processing PDF document" in str(excinfo.value)
    
    @patch('src.docling_integration.serialize_docling_document')
    def test_save_output_error_handling(self, mock_serialize):
        """Test error handling in save_output."""
        # Set up mock to raise an exception
        mock_serialize.side_effect = TypeError("Serialization failed")
        
        # Call the function and expect an exception
        with pytest.raises(TypeError) as excinfo:
            save_output(self.mock_document, self.output_dir)
        
        # Verify error message
        assert "DoclingDocument export failed" in str(excinfo.value)

class TestParseHelper(unittest.TestCase):
    """Test cases for parse_helper functions"""
    
    def test_process_extracted_images(self):
        """Test that process_extracted_images correctly sets external file paths"""
        # Create test data with raw image data
        test_image_data = b'Test image binary data'
        test_images_data = {
            "images": [
                {
                    "raw_data": test_image_data,
                    "data_uri": f"data:image/png;base64,{base64.b64encode(test_image_data).decode('utf-8')}",
                    "metadata": {
                        "id": "test_image_1",
                        "format": "image/png",
                        "description": "Test image"
                    }
                }
            ]
        }
        
        # Create temporary directories for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            output_path = temp_dir_path
            images_dir = temp_dir_path / "images"
            images_dir.mkdir(exist_ok=True)
            
            # Process the images
            process_extracted_images(test_images_data, images_dir, output_path)
            
            # Check that the file was saved
            expected_file_path = images_dir / "test_image_1.png"
            self.assertTrue(expected_file_path.exists(), f"Image file not found at {expected_file_path}")
            
            # Check that the raw_data was removed
            self.assertNotIn("raw_data", test_images_data["images"][0], "raw_data should be removed")
            
            # Check that file_path was set in metadata
            self.assertIn("file_path", test_images_data["images"][0]["metadata"], "file_path missing in metadata")
            expected_relative_path = str(Path("images") / "test_image_1.png")
            self.assertEqual(test_images_data["images"][0]["metadata"]["file_path"], expected_relative_path)
            
            # Check that external_path was set
            self.assertIn("external_path", test_images_data["images"][0], "external_path missing")
            self.assertEqual(test_images_data["images"][0]["external_path"], expected_relative_path)
            
            # Check that images_data.json was created
            json_path = output_path / "images_data.json"
            self.assertTrue(json_path.exists(), f"images_data.json not found at {json_path}")
            
            # Verify the content of the JSON file
            with open(json_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                self.assertEqual(
                    saved_data["images"][0]["external_path"], 
                    expected_relative_path,
                    "external_path in saved JSON doesn't match expected"
                )

if __name__ == "__main__":
    unittest.main() 