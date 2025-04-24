"""
Test module for format_standardized_output.py

This module contains unit tests for the format_standardized_output functions.
"""

import os
import json
import unittest
from pathlib import Path
import tempfile
import shutil

# Import the module to test
from src.format_standardized_output import (
    is_furniture,
    extract_content_type,
    format_text_block,
    format_table_block,
    build_chunk,
    save_standardized_output
)

class TestFormatStandardizedOutput(unittest.TestCase):
    """Test cases for format_standardized_output.py functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Sample element data
        self.text_element = {
            "type": "text",
            "text_content": "Sample text content",
            "content_layer": "body",
            "extracted_metadata": {
                "breadcrumb": "Section > Subsection",
                "page_no": 1,
                "bbox_raw": {"l": 50, "t": 100, "r": 300, "b": 150}
            }
        }
        
        self.furniture_element = {
            "type": "text",
            "text_content": "Header text",
            "content_layer": "furniture"
        }
        
        self.image_element = {
            "type": "picture",
            "content_layer": "body",
            "external_path": "images/sample.png",
            "context_before": "Text before image",
            "context_after": "Text after image",
            "extracted_metadata": {
                "breadcrumb": "Section > Subsection",
                "page_no": 2,
                "bbox_raw": {"l": 100, "t": 200, "r": 300, "b": 400},
                "image_ocr_text": "Text extracted from image"
            }
        }
        
        self.table_element = {
            "type": "table",
            "content_layer": "body",
            "table_content": [["Header1", "Header2"], ["Row1Col1", "Row1Col2"]],
            "extracted_metadata": {
                "breadcrumb": "Section > Tables",
                "page_no": 3,
                "bbox_raw": {"l": 50, "t": 300, "r": 400, "b": 450}
            }
        }
        
        # Sample document data
        self.document_data = {
            "name": "test_document",
            "element_map": {
                "flattened_sequence": [
                    self.text_element,
                    self.furniture_element,
                    self.image_element,
                    self.table_element
                ]
            }
        }
    
    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_is_furniture(self):
        """Test is_furniture function."""
        self.assertFalse(is_furniture(self.text_element))
        self.assertTrue(is_furniture(self.furniture_element))
        self.assertFalse(is_furniture(self.image_element))
        self.assertFalse(is_furniture(self.table_element))
    
    def test_extract_content_type(self):
        """Test extract_content_type function."""
        self.assertEqual(extract_content_type(self.text_element), "text")
        self.assertEqual(extract_content_type(self.image_element), "image")
        self.assertEqual(extract_content_type(self.table_element), "table")
    
    def test_format_text_block(self):
        """Test format_text_block function."""
        # Test text element
        text_block = format_text_block(self.text_element, "Section > Subsection")
        self.assertIn("Section > Subsection", text_block)
        self.assertIn("Sample text content", text_block)
        
        # Test image element with breadcrumb
        image_block = format_text_block(self.image_element, "Section > Subsection")
        self.assertIn("Section > Subsection", image_block)
        self.assertIn("Text before image", image_block)
        self.assertIn("[Image Text:", image_block)
        self.assertIn("Text extracted from image", image_block)
        self.assertIn("Text after image", image_block)
    
    def test_format_table_block(self):
        """Test format_table_block function."""
        # Test table element
        table_block = format_table_block(self.table_element)
        self.assertIsNotNone(table_block)
        table_data = json.loads(table_block)
        self.assertEqual(len(table_data), 2) # Two rows
        self.assertEqual(table_data[0][0], "Header1")
        
        # Test non-table element
        self.assertIsNone(format_table_block(self.text_element))
    
    def test_build_chunk(self):
        """Test build_chunk function."""
        source_metadata = {
            "filename": "test.pdf",
            "mimetype": "application/pdf"
        }
        
        # Test text chunk
        text_chunk = build_chunk(self.text_element, 1, None, source_metadata)
        self.assertEqual(text_chunk["content_type"], "text")
        self.assertEqual(text_chunk["block_id"], 1)
        self.assertEqual(text_chunk["master_index"], 1)
        self.assertEqual(text_chunk["coords_x"], 50)
        self.assertEqual(text_chunk["coords_y"], 100)
        self.assertEqual(text_chunk["coords_cx"], 250)
        self.assertEqual(text_chunk["coords_cy"], 50)
        
        # Test image chunk
        image_chunk = build_chunk(self.image_element, 2, None, source_metadata)
        self.assertEqual(image_chunk["content_type"], "image")
        self.assertEqual(image_chunk["external_files"], "images/sample.png")
        self.assertEqual(image_chunk["master_index"], 2)
        
        # Test table chunk
        table_chunk = build_chunk(self.table_element, 3, None, source_metadata)
        self.assertEqual(table_chunk["content_type"], "table")
        self.assertIsNotNone(table_chunk["table_block"])
    
    def test_save_standardized_output(self):
        """Test save_standardized_output function."""
        output_file = save_standardized_output(
            self.document_data,
            self.temp_dir,
            "test.pdf"
        )
        
        # Check that the file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Load and check the contents
        with open(output_file, 'r') as f:
            output_data = json.load(f)
        
        # Check structure
        self.assertIn("chunks", output_data)
        self.assertIn("furniture", output_data)
        self.assertIn("source_metadata", output_data)
        
        # Check furniture
        self.assertEqual(len(output_data["furniture"]), 1)
        self.assertEqual(output_data["furniture"][0], "Header text")
        
        # Check chunks
        self.assertEqual(len(output_data["chunks"]), 3)  # Excluding furniture
        
        # Check chunk fields
        chunk_types = [chunk["content_type"] for chunk in output_data["chunks"]]
        self.assertIn("text", chunk_types)
        self.assertIn("image", chunk_types)
        self.assertIn("table", chunk_types)
        
        # Check metadata
        self.assertEqual(output_data["source_metadata"]["filename"], "test.pdf")
        self.assertEqual(output_data["source_metadata"]["mimetype"], "application/pdf")


if __name__ == '__main__':
    unittest.main() 