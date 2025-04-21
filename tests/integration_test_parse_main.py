"""
Integration tests for the PDF document parsing application.

These tests verify that the parse_main.py functions work together correctly
and that content extraction is properly integrated.
"""

import os
import sys
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Mock the docling imports before importing parse_main
sys.modules['docling'] = MagicMock()
sys.modules['docling.document_converter'] = MagicMock()
sys.modules['docling.datamodel.base_models'] = MagicMock()
sys.modules['docling.datamodel.pipeline_options'] = MagicMock()
sys.modules['docling.document_converter.DocumentConverter'] = MagicMock()
sys.modules['docling.datamodel.base_models.InputFormat'] = MagicMock()
sys.modules['docling.document_converter.PdfFormatOption'] = MagicMock()
sys.modules['docling.datamodel.pipeline_options.PdfPipelineOptions'] = MagicMock()

# Now import the modules to test
import parse_main
from content_extractor import (
    extract_text_content, 
    extract_table_content, 
    extract_image_content
)

class MockPage:
    """Mock implementation of a docling Page."""
    
    def __init__(self, page_id, segments=None, tables=None, pictures=None):
        self.id = page_id
        self.self_ref = f"page_{page_id}"
        self.segments = segments or []
        self.tables = tables or []
        self.pictures = pictures or []
        # Make all properties dictionary-like for JSON serialization
        self.metadata = {"type": "page"}
        
    def to_dict(self):
        """Return a serializable dictionary representation of this page."""
        return {
            "id": self.id,
            "self_ref": self.self_ref,
            "metadata": self.metadata,
            "segments": [s.to_dict() for s in self.segments],
            "tables": [t.to_dict() for t in self.tables],
            "pictures": [p.to_dict() for p in self.pictures]
        }

class MockSegment:
    """Mock implementation of a docling Segment."""
    
    def __init__(self, page_id, segment_id, text="Sample text"):
        self.id = segment_id
        self.self_ref = f"page_{page_id}_segment_{segment_id}"
        self.text = text
        self.metadata = {"type": "segment"}
        
    def to_dict(self):
        """Return a serializable dictionary representation of this segment."""
        return {
            "id": self.id,
            "self_ref": self.self_ref,
            "text": self.text,
            "metadata": self.metadata
        }

class MockTable:
    """Mock implementation of a docling Table."""
    
    def __init__(self, page_id, table_id):
        self.id = table_id
        self.self_ref = f"page_{page_id}_table_{table_id}"
        self.cells = [
            {"row": 0, "col": 0, "text": "Cell 1"},
            {"row": 0, "col": 1, "text": "Cell 2"},
            {"row": 1, "col": 0, "text": "Cell 3"},
            {"row": 1, "col": 1, "text": "Cell 4"}
        ]
        self.metadata = {"type": "table"}
        
    def to_dict(self):
        """Return a serializable dictionary representation of this table."""
        return {
            "id": self.id,
            "self_ref": self.self_ref,
            "cells": self.cells,
            "metadata": self.metadata
        }

class MockPicture:
    """Mock implementation of a docling Picture."""
    
    def __init__(self, page_id, picture_id):
        self.id = picture_id
        self.self_ref = f"page_{page_id}_picture_{picture_id}"
        self.image_path = f"images/page_{page_id}_image_{picture_id}.jpg"
        self.description = f"Sample image {picture_id} on page {page_id}"
        self.metadata = {"type": "picture"}
        
    def to_dict(self):
        """Return a serializable dictionary representation of this picture."""
        return {
            "id": self.id,
            "self_ref": self.self_ref,
            "image_path": self.image_path,
            "description": self.description,
            "metadata": self.metadata
        }

class MockDoclingDocument:
    """Mock implementation of a docling Document."""
    
    def __init__(self, name="test_document"):
        self.name = name
        self.schema_version = "1.0"
        
        # Create some pages with content
        self.pages = []
        for page_id in range(1, 3):
            segments = [MockSegment(page_id, i) for i in range(1, 4)]
            tables = [MockTable(page_id, 1)]
            pictures = [MockPicture(page_id, 1)]
            
            page = MockPage(page_id, segments, tables, pictures)
            self.pages.append(page)
    
    def export_to_dict(self):
        """Return a serializable dictionary representation of this document."""
        return {
            "name": self.name,
            "schema_version": self.schema_version,
            "pages": [page.to_dict() for page in self.pages]
        }

@patch('parse_main.DocumentConverter')
class TestParseMainIntegration(unittest.TestCase):
    """Integration tests for parse_main.py with content extraction."""
    
    def setUp(self):
        """Set up test data and environment."""
        # Create a temporary directory for output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Create a mock DoclingDocument
        self.mock_document = MockDoclingDocument()
        
        # Mock the conversion result
        self.mock_conversion_result = MagicMock()
        self.mock_conversion_result.status = "success"
        self.mock_conversion_result.document = self.mock_document
    
    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()
    
    def test_process_and_save_with_content_extraction(self, mock_converter_class):
        """Test that processing and saving works with content extraction."""
        # Configure the mock
        mock_instance = mock_converter_class.return_value
        mock_instance.convert.return_value = self.mock_conversion_result
        
        # Create a dummy PDF path
        pdf_path = self.output_dir / "dummy.pdf"
        with open(pdf_path, 'w') as f:
            f.write("Dummy PDF content")
        
        # Process the document
        document = parse_main.process_pdf_document(pdf_path, self.output_dir)
        
        # Make sure the converter was called
        mock_instance.convert.assert_called_once()
        
        # Verify we got back the mock document
        self.assertEqual(document, self.mock_document)
        
        # Now save the output
        output_file = parse_main.save_output(document, self.output_dir)
        
        # Check that the file was created
        self.assertTrue(output_file.exists())
        
        # Load the JSON and verify it has the expected structure
        with open(output_file, 'r') as f:
            doc_dict = json.load(f)
        
        # Verify basic document structure exists instead of element_map
        self.assertIn('pages', doc_dict)
        self.assertIn('name', doc_dict)
        self.assertIn('schema_version', doc_dict)
    
    def test_content_extraction_functions(self, mock_converter_class):
        """Test that the content extraction functions work correctly."""
        # Create sample elements
        text_element = {
            "id": "text_1", 
            "text": "Sample text content", 
            "metadata": {"type": "paragraph"}
        }
        
        table_element = {
            "id": "table_1",
            "metadata": {"type": "table"},
            "cells": [
                {"row": 0, "col": 0, "text": "Header", "rowspan": 1, "colspan": 1},
                {"row": 1, "col": 0, "text": "Data", "rowspan": 1, "colspan": 1}
            ]
        }
        
        image_element = {
            "id": "image_1",
            "metadata": {"type": "picture"},
            "image_path": "/path/to/image.jpg",
            "bounds": {"x": 0, "y": 0, "width": 100, "height": 100}
        }
        
        # Test text extraction
        text_content = extract_text_content(text_element)
        self.assertEqual(text_content, "Sample text content")
        
        # Test table extraction
        table_content = extract_table_content(table_element)
        self.assertEqual(len(table_content), 2)  # 2 rows
        self.assertEqual(table_content[0][0], "Header")
        self.assertEqual(table_content[1][0], "Data")
        
        # Test image extraction
        image_content = extract_image_content(image_element)
        self.assertEqual(image_content["image_path"], "/path/to/image.jpg")
    
    def test_main_function_integration(self, mock_converter_class):
        """Test the main function with content extraction."""
        # Configure the mock
        mock_instance = mock_converter_class.return_value
        mock_instance.convert.return_value = self.mock_conversion_result
        
        # Create a dummy PDF path
        pdf_path = self.output_dir / "dummy.pdf"
        with open(pdf_path, 'w') as f:
            f.write("Dummy PDF content")
        
        # Mock the command line arguments
        with patch('sys.argv', ['parse_main.py', 
                              '--pdf_path', str(pdf_path),
                              '--output_dir', str(self.output_dir)]):
            
            # Patch os.path.exists to make it think the PDF exists
            with patch('os.path.exists', return_value=True):
                # Call the main function
                return_code = parse_main.main()
                
                # Check if it completed successfully
                self.assertEqual(return_code, 0)
                
                # Verify output file was created
                output_files = list(self.output_dir.glob('*.json'))
                self.assertGreater(len(output_files), 0)
                
                # Check content of first output file
                with open(output_files[0], 'r') as f:
                    doc_dict = json.load(f)
                
                # Verify basic document structure exists instead of element_map
                self.assertIn('pages', doc_dict)
                self.assertIn('name', doc_dict)
                self.assertIn('schema_version', doc_dict)


if __name__ == '__main__':
    unittest.main() 