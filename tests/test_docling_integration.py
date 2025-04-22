"""
Tests for docling_integration.py

This module contains tests for the docling_integration.py module, which provides 
helper functions for interacting with the docling library.
"""

import os
import sys
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

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

# Import docling_integration module
from src.docling_integration import (
    create_pdf_pipeline_options,
    convert_pdf_document,
    extract_document_metadata,
    serialize_docling_document,
    merge_with_image_data
)

class TestDoclingIntegration:
    """Test suite for docling_integration.py module."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary PDF file
        self.temp_dir = tempfile.TemporaryDirectory()
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
        # Mock the export_to_dict method to return a test dictionary
        self.mock_document.export_to_dict.return_value = {
            "name": "test_document",
            "pages": [{"id": "page_1"}, {"id": "page_2"}]
        }
        
        # Setup page objects with tables and pictures for metadata extraction
        self.page1 = MagicMock()
        self.page1.tables = [MagicMock(), MagicMock()]
        self.page1.pictures = [MagicMock()]
        
        self.page2 = MagicMock()
        self.page2.tables = []
        self.page2.pictures = [MagicMock(), MagicMock()]
        
        self.mock_document_with_content = MagicMock()
        self.mock_document_with_content.name = "test_document_with_content"
        self.mock_document_with_content.pages = [self.page1, self.page2]
        self.mock_document_with_content.metadata = {
            "author": "Test Author",
            "created": "2023-01-01"
        }
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_create_pdf_pipeline_options_default(self):
        """Test creating PDF pipeline options with default values."""
        # Import the PdfPipelineOptions class
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        
        # Mock PdfPipelineOptions class
        mock_options = MagicMock()
        PdfPipelineOptions.return_value = mock_options
        
        # Call the function
        options = create_pdf_pipeline_options()
        
        # Verify options were set correctly
        assert options is mock_options
        assert mock_options.images_scale == 2.0
        assert mock_options.generate_page_images is True
        assert mock_options.generate_picture_images is True
        assert mock_options.do_picture_description is True
        assert mock_options.do_table_structure is True
        assert mock_options.allow_external_plugins is True
    
    def test_create_pdf_pipeline_options_custom(self):
        """Test creating PDF pipeline options with custom values."""
        # Import the PdfPipelineOptions class
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        
        # Mock PdfPipelineOptions class
        mock_options = MagicMock()
        PdfPipelineOptions.return_value = mock_options
        
        # Call the function with custom values
        options = create_pdf_pipeline_options(
            images_scale=3.0,
            generate_page_images=False,
            generate_picture_images=False,
            custom_option="test"  # This should be ignored
        )
        
        # Verify options were set correctly
        assert options is mock_options
        assert mock_options.images_scale == 3.0
        assert mock_options.generate_page_images is False
        assert mock_options.generate_picture_images is False
        assert mock_options.do_picture_description is True  # Default
        assert mock_options.do_table_structure is True  # Default
        assert mock_options.allow_external_plugins is True  # Default
    
    @patch('docling.document_converter.DocumentConverter')
    def test_convert_pdf_document_success(self, mock_document_converter):
        """Test successful PDF conversion."""
        # Import required classes
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import PdfFormatOption
        
        # Set up mocks
        mock_converter = MagicMock()
        mock_document_converter.return_value = mock_converter
        
        mock_result = MagicMock()
        mock_result.status = "success"
        mock_result.document = self.mock_document
        mock_converter.convert.return_value = mock_result
        
        # Call the function
        result = convert_pdf_document(self.pdf_path)
        
        # Verify results
        assert result is self.mock_document
        mock_converter.convert.assert_called_once()
    
    @patch('docling.document_converter.DocumentConverter')
    def test_convert_pdf_document_failure(self, mock_document_converter):
        """Test PDF conversion failure."""
        # Set up mocks
        mock_converter = MagicMock()
        mock_document_converter.return_value = mock_converter
        
        mock_result = MagicMock()
        mock_result.status = "failure"
        mock_converter.convert.return_value = mock_result
        
        # Call the function and expect an exception
        with pytest.raises(RuntimeError) as excinfo:
            convert_pdf_document(self.pdf_path)
        
        # Verify error message
        assert "PDF conversion failed" in str(excinfo.value)
    
    @patch('pathlib.Path.exists')
    def test_convert_pdf_document_file_not_found(self, mock_exists):
        """Test PDF conversion with non-existent file."""
        # Set up mocks
        mock_exists.return_value = False
        
        # Call the function and expect an exception
        with pytest.raises(FileNotFoundError) as excinfo:
            convert_pdf_document("nonexistent.pdf")
        
        # Verify error message
        assert "PDF file not found" in str(excinfo.value)
    
    @patch('docling.document_converter.DocumentConverter')
    @patch('builtins.open', new_callable=mock_open, read_data='{"pdf_pipeline_options": {"images_scale": 3.0}}')
    def test_convert_pdf_document_with_config(self, mock_file, mock_document_converter):
        """Test PDF conversion with config file."""
        # Set up mocks
        mock_converter = MagicMock()
        mock_document_converter.return_value = mock_converter
        
        mock_result = MagicMock()
        mock_result.status = "success"
        mock_result.document = self.mock_document
        mock_converter.convert.return_value = mock_result
        
        # Call the function
        result = convert_pdf_document(self.pdf_path, config_file=self.config_path)
        
        # Verify results
        assert result is self.mock_document
        mock_file.assert_called_once_with(self.config_path, 'r')
    
    def test_extract_document_metadata_basic(self):
        """Test extracting basic metadata from a document."""
        # Call the function
        metadata = extract_document_metadata(self.mock_document)
        
        # Verify results
        assert metadata["name"] == "test_document"
        assert metadata["page_count"] == 2
        assert metadata["has_tables"] is False
        assert metadata["has_pictures"] is False
        assert metadata["has_forms"] is False
    
    def test_extract_document_metadata_with_content(self):
        """Test extracting metadata from a document with tables and pictures."""
        # Call the function
        metadata = extract_document_metadata(self.mock_document_with_content)
        
        # Verify results
        assert metadata["name"] == "test_document_with_content"
        assert metadata["page_count"] == 2
        assert metadata["has_tables"] is True
        assert metadata["has_pictures"] is True
        assert metadata["table_count"] == 2
        assert metadata["picture_count"] == 3
        assert metadata["author"] == "Test Author"
        assert metadata["created"] == "2023-01-01"
    
    def test_serialize_docling_document_success(self):
        """Test successful document serialization."""
        # Call the function
        result = serialize_docling_document(self.mock_document)
        
        # Verify results
        assert result == {
            "name": "test_document",
            "pages": [{"id": "page_1"}, {"id": "page_2"}]
        }
        self.mock_document.export_to_dict.assert_called_once()
    
    def test_serialize_docling_document_no_export_method(self):
        """Test document serialization fallback when export_to_dict is not available."""
        # Create a mock document without export_to_dict method
        mock_doc = MagicMock()
        del mock_doc.export_to_dict
        mock_doc.dict.return_value = {"name": "fallback_doc"}
        
        # Call the function
        result = serialize_docling_document(mock_doc)
        
        # Verify results
        assert result == {"name": "fallback_doc"}
        mock_doc.dict.assert_called_once()
    
    def test_serialize_docling_document_error(self):
        """Test document serialization error handling."""
        # Create a mock document that raises an exception
        mock_doc = MagicMock()
        mock_doc.export_to_dict.side_effect = Exception("Serialization error")
        mock_doc.dict.side_effect = Exception("Dict conversion error")
        
        # Call the function and expect an exception
        with pytest.raises(TypeError) as excinfo:
            serialize_docling_document(mock_doc)
        
        # Verify error message
        assert "Failed to serialize DoclingDocument" in str(excinfo.value)
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"images": [{"id": "img1"}]}')
    def test_merge_with_image_data_success(self, mock_file, mock_exists):
        """Test successful image data merging."""
        # Set up mocks
        mock_exists.return_value = True
        
        # Create a document dictionary
        doc_dict = {"name": "test_doc", "pages": []}
        
        # Call the function
        result = merge_with_image_data(doc_dict, "images_data.json")
        
        # Verify results
        assert result["name"] == "test_doc"
        assert "images_data" in result
        assert result["images_data"] == {"images": [{"id": "img1"}]}
        mock_file.assert_called_once_with("images_data.json", 'r', encoding='utf-8')
    
    @patch('pathlib.Path.exists')
    def test_merge_with_image_data_file_not_found(self, mock_exists):
        """Test image data merging when file is not found."""
        # Set up mocks
        mock_exists.return_value = False
        
        # Create a document dictionary
        doc_dict = {"name": "test_doc", "pages": []}
        
        # Call the function
        result = merge_with_image_data(doc_dict, "nonexistent.json")
        
        # Verify results - should return the original dict unchanged
        assert result == doc_dict
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_merge_with_image_data_error(self, mock_file, mock_exists):
        """Test image data merging error handling."""
        # Set up mocks
        mock_exists.return_value = True
        
        # Create a document dictionary
        doc_dict = {"name": "test_doc", "pages": []}
        
        # Call the function
        result = merge_with_image_data(doc_dict, "images_data.json")
        
        # Verify results - should return the original dict unchanged
        assert result == doc_dict
        mock_file.assert_called_once_with("images_data.json", 'r', encoding='utf-8') 