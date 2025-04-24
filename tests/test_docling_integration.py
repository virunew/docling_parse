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
import unittest

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Add src directory to path for imports
src_dir = os.path.join(parent_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

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

class TestDoclingIntegration(unittest.TestCase):
    """Test cases for the docling_integration module."""
    
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
    
    def test_create_pdf_pipeline_options(self):
        """Test that PDF pipeline options are created correctly."""
        # Create pipeline options with default values
        options = create_pdf_pipeline_options()
        
        # Check default values
        self.assertEqual(options.images_scale, 2.0)
        self.assertTrue(options.generate_page_images)
        self.assertTrue(options.generate_picture_images)
        self.assertTrue(options.do_picture_description)
        self.assertTrue(options.do_table_structure)
        self.assertTrue(options.allow_external_plugins)
        
        # Create pipeline options with custom values
        custom_options = create_pdf_pipeline_options(
            images_scale=1.5,
            generate_page_images=False,
            generate_picture_images=False
        )
        
        # Check custom values
        self.assertEqual(custom_options.images_scale, 1.5)
        self.assertFalse(custom_options.generate_page_images)
        self.assertFalse(custom_options.generate_picture_images)
        self.assertTrue(custom_options.do_picture_description)  # Default value
        
    def test_serialize_docling_document_with_dictionary(self):
        """Test that serialize_docling_document handles dictionaries correctly."""
        # Create a test dictionary
        test_dict = {
            "source_metadata": {"filename": "test.pdf"},
            "texts": [{"self_ref": "#/texts/0", "text": "Test"}],
            "element_map": {"texts_0": {"self_ref": "#/texts/0"}}
        }
        
        # Serialize the dictionary
        result = serialize_docling_document(test_dict)
        
        # The result should be the same dictionary
        self.assertEqual(result, test_dict)
        self.assertIs(result, test_dict)  # Verify it's the same object
    
    def test_serialize_docling_document_with_document_object(self):
        """Test that serialize_docling_document handles DoclingDocument objects correctly."""
        # Create a mock DoclingDocument with the export_to_dict method
        mock_doc = MagicMock()
        mock_doc.export_to_dict.return_value = {"test": "data"}
        
        # Serialize the mock document
        result = serialize_docling_document(mock_doc)
        
        # The result should be the dictionary from export_to_dict
        self.assertEqual(result, {"test": "data"})
        mock_doc.export_to_dict.assert_called_once()
        
        # Create a mock DoclingDocument without the export_to_dict method
        mock_doc2 = MagicMock()
        del mock_doc2.export_to_dict
        mock_doc2.dict.return_value = {"test": "fallback"}
        
        # Serialize the mock document
        result = serialize_docling_document(mock_doc2)
        
        # The result should be the dictionary from dict()
        self.assertEqual(result, {"test": "fallback"})
        mock_doc2.dict.assert_called_once()
    
    def test_merge_with_image_data(self):
        """Test that merge_with_image_data correctly merges image data."""
        # Create a temporary file with image data
        import tempfile
        temp_dir = tempfile.mkdtemp()
        try:
            image_data = {
                "images": [
                    {"id": "img1", "path": "images/img1.png"},
                    {"id": "img2", "path": "images/img2.png"}
                ]
            }
            
            # Write image data to a temporary file
            image_data_path = Path(temp_dir) / "images_data.json"
            with open(image_data_path, 'w') as f:
                json.dump(image_data, f)
            
            # Create a document dictionary
            doc_dict = {
                "texts": [{"text": "Test document"}]
            }
            
            # Merge the document with image data
            result = merge_with_image_data(doc_dict, image_data_path)
            
            # Check that the image data was merged correctly
            self.assertIn("images_data", result)
            self.assertEqual(result["images_data"], image_data)
            self.assertIn("texts", result)  # Original data is preserved
            
            # Test with non-existent file
            result = merge_with_image_data(doc_dict, "non_existent_file.json")
            self.assertEqual(result, doc_dict)  # Returns original dictionary if file not found
            
        finally:
            # Clean up temporary directory
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main() 