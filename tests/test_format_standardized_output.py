"""
Unit test for the format_standardized_output module.

This module tests the functionality of the format_standardized_output module,
which converts document data into a standardized format compatible with SQL databases.
"""

import os
import json
import unittest
import tempfile
from pathlib import Path
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test
from src.format_standardized_output import (
    save_standardized_output, 
    build_chunk, 
    format_text_block, 
    format_table_block,
    is_furniture,
    extract_content_type
)


class TestFormatStandardizedOutput(unittest.TestCase):
    """Test cases for the format_standardized_output module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create sample document data
        self.sample_document = {
            "name": "test_document",
            "metadata": {
                "filename": "test_document.pdf",
                "mimetype": "application/pdf",
                "binary_hash": "abc123"
            },
            "element_map": {
                "flattened_sequence": [
                    # Text element
                    {
                        "type": "text",
                        "text_content": "This is a sample text paragraph.",
                        "content_layer": "content",
                        "extracted_metadata": {
                            "breadcrumb": "Document > Section > Subsection",
                            "bbox_raw": {"l": 50, "t": 100, "r": 550, "b": 150},
                            "page_no": 1
                        }
                    },
                    # Furniture element
                    {
                        "type": "header",
                        "text_content": "Header Text",
                        "content_layer": "furniture",
                        "extracted_metadata": {
                            "bbox_raw": {"l": 50, "t": 50, "r": 550, "b": 80},
                            "page_no": 1
                        }
                    },
                    # Table element
                    {
                        "type": "table",
                        "table_content": [["Header1", "Header2"], ["Value1", "Value2"]],
                        "content_layer": "content",
                        "extracted_metadata": {
                            "breadcrumb": "Document > Section > Tables",
                            "caption": "Sample Table",
                            "bbox_raw": {"l": 50, "t": 200, "r": 550, "b": 300},
                            "page_no": 2
                        }
                    },
                    # Image element
                    {
                        "type": "picture",
                        "context_before": "Text before the image.",
                        "ocr_text": "Text extracted from image via OCR",
                        "context_after": "Text after the image.",
                        "external_path": "/path/to/images/test_image.png",
                        "content_layer": "content",
                        "extracted_metadata": {
                            "breadcrumb": "Document > Section > Images",
                            "caption": "Sample Image",
                            "bbox_raw": {"l": 100, "t": 150, "r": 500, "b": 450},
                            "page_no": 3,
                            "image_width": 400,
                            "image_height": 300,
                            "image_mimetype": "image/png"
                        }
                    }
                ]
            }
        }
        
        # Create temp directory for output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name
    
    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def test_is_furniture(self):
        """Test the is_furniture function."""
        # Get elements from sample document
        elements = self.sample_document["element_map"]["flattened_sequence"]
        
        # Test furniture element
        self.assertTrue(is_furniture(elements[1]))
        
        # Test content elements
        self.assertFalse(is_furniture(elements[0]))
        self.assertFalse(is_furniture(elements[2]))
        self.assertFalse(is_furniture(elements[3]))
    
    def test_extract_content_type(self):
        """Test the extract_content_type function."""
        # Get elements from sample document
        elements = self.sample_document["element_map"]["flattened_sequence"]
        
        # Check content types
        self.assertEqual("text", extract_content_type(elements[0]))
        self.assertEqual("text", extract_content_type(elements[1]))  # Header is text type
        self.assertEqual("table", extract_content_type(elements[2]))
        self.assertEqual("image", extract_content_type(elements[3]))
    
    def test_format_text_block(self):
        """Test the format_text_block function."""
        # Get text element
        text_element = self.sample_document["element_map"]["flattened_sequence"][0]
        
        # Format text block
        text_block = format_text_block(text_element, "Document > Section > Subsection")
        
        # Check for breadcrumb and text content
        self.assertIn("Document > Section > Subsection", text_block)
        self.assertIn("This is a sample text paragraph.", text_block)
        
        # Test image element
        image_element = self.sample_document["element_map"]["flattened_sequence"][3]
        image_block = format_text_block(image_element, "Document > Section > Images")
        
        # Check for image-specific content
        self.assertIn("Text before the image.", image_block)
        self.assertIn("[Image Text: Text extracted from image via OCR]", image_block)
        self.assertIn("Text after the image.", image_block)
    
    def test_format_table_block(self):
        """Test the format_table_block function."""
        # Get table element
        table_element = self.sample_document["element_map"]["flattened_sequence"][2]
        
        # Format table block
        table_block = format_table_block(table_element)
        
        # Check table format
        self.assertIsNotNone(table_block)
        table_data = json.loads(table_block)
        self.assertEqual(2, len(table_data))
        self.assertEqual(2, len(table_data[0]))
        self.assertEqual("Header1", table_data[0][0])
        self.assertEqual("Value2", table_data[1][1])
        
        # Test with non-table element
        text_element = self.sample_document["element_map"]["flattened_sequence"][0]
        self.assertIsNone(format_table_block(text_element))
    
    def test_build_chunk(self):
        """Test the build_chunk function."""
        # Get elements
        text_element = self.sample_document["element_map"]["flattened_sequence"][0]
        
        # Build a chunk
        source_metadata = self.sample_document["metadata"]
        chunk = build_chunk(text_element, 1, "test-doc-001", source_metadata)
        
        # Verify required fields
        required_fields = [
            "_id", "block_id", "doc_id", "content_type", "file_type", 
            "master_index", "master_index2", "coords_x", "coords_y", 
            "coords_cx", "coords_cy", "author_or_speaker", "added_to_collection", 
            "file_source", "table_block", "modified_date", "created_date", 
            "creator_tool", "external_files", "text_block", "header_text", 
            "text_search", "user_tags", "special_field1", "special_field2", 
            "special_field3", "graph_status", "dialog", "embedding_flags", "metadata"
        ]
        
        for field in required_fields:
            self.assertIn(field, chunk)
        
        # Check specific values
        self.assertEqual(1, chunk["block_id"])
        self.assertEqual("test-doc-001", chunk["doc_id"])
        self.assertEqual("text", chunk["content_type"])
        self.assertEqual("application/pdf", chunk["file_type"])
        self.assertEqual(1, chunk["master_index"])
        self.assertEqual(50, chunk["coords_x"])
        self.assertEqual(100, chunk["coords_y"])
        self.assertEqual(500, chunk["coords_cx"])
        self.assertEqual(50, chunk["coords_cy"])
        self.assertEqual("test_document.pdf", chunk["file_source"])
        self.assertIn("This is a sample text paragraph.", chunk["text_block"])
        self.assertEqual("Document > Section > Subsection", chunk["header_text"])
        self.assertEqual("This is a sample text paragraph.", chunk["text_search"])
        
        # Test with image element
        image_element = self.sample_document["element_map"]["flattened_sequence"][3]
        image_chunk = build_chunk(image_element, 2, "test-doc-001", source_metadata)
        
        # Check image-specific fields
        self.assertEqual("image", image_chunk["content_type"])
        self.assertEqual("/path/to/images/test_image.png", image_chunk["external_files"])
        self.assertIn("[Image Text: Text extracted from image via OCR]", image_chunk["text_block"])
    
    def test_save_standardized_output(self):
        """Test the save_standardized_output function."""
        # Create a temporary PDF path for the test
        pdf_path = os.path.join(self.temp_dir.name, "test_document.pdf")
        
        # Create an empty file
        with open(pdf_path, 'w') as f:
            f.write("dummy pdf content")
        
        # Save standardized output
        output_file = save_standardized_output(
            self.sample_document,
            self.output_dir,
            pdf_path
        )
        
        # Check that the file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Load the output and validate its structure
        with open(output_file, 'r', encoding='utf-8') as f:
            output_data = json.load(f)
        
        # Check the output structure
        self.assertIn("chunks", output_data)
        self.assertIn("furniture", output_data)
        self.assertIn("source_metadata", output_data)
        
        # Check source metadata
        self.assertEqual("test_document.pdf", output_data["source_metadata"]["filename"])
        self.assertEqual("application/pdf", output_data["source_metadata"]["mimetype"])
        
        # Check furniture
        self.assertIn("Header Text", output_data["furniture"])
        
        # Check chunks - should have 3 (text, table, image)
        self.assertEqual(3, len(output_data["chunks"]))
        
        # Validate chunk structure and content
        for chunk in output_data["chunks"]:
            # Check required fields
            required_fields = [
                "block_id", "content_type", "file_type", "master_index", 
                "coords_x", "coords_y", "coords_cx", "coords_cy", 
                "text_block", "header_text"
            ]
            for field in required_fields:
                self.assertIn(field, chunk)
            
            # Additional checks for specific content types
            if chunk["content_type"] == "text":
                self.assertIn("This is a sample text paragraph.", chunk["text_block"])
            elif chunk["content_type"] == "table":
                self.assertIsNotNone(chunk["table_block"])
            elif chunk["content_type"] == "image":
                self.assertIsNotNone(chunk["external_files"])
                self.assertIn("[Image Text:", chunk["text_block"])


if __name__ == "__main__":
    unittest.main() 