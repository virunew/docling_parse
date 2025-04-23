"""
Test cases for the SQL formatter module.

This module tests the functionality of the SQL formatter, which converts
Docling document data into a standardized JSON format suitable for SQL database ingestion.
"""
import json
import os
import sys
import unittest
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test
from src.sql_formatter import process_docling_json_to_sql_format


class TestSQLFormatter(unittest.TestCase):
    """Test cases for the SQL formatter functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a sample document data dictionary for testing
        self.sample_document = {
            "metadata": {
                "filename": "test_document.pdf",
                "mimetype": "application/pdf",
                "binary_hash": "abc123"
            },
            "furniture": [
                {"text": "Header Text", "type": "header"},
                {"text": "Footer Text", "type": "footer"},
                {"text": "Page Number", "type": "page_number"}
            ],
            "body": [
                # Text element
                {
                    "type": "text",
                    "text": "This is a sample text paragraph.",
                    "breadcrumb": "Document > Section > Subsection",
                    "prov": {
                        "page_no": 1,
                        "bbox": {"l": 50, "t": 100, "r": 550, "b": 150}
                    },
                    "self_ref": "#/texts/0"
                },
                # Table element
                {
                    "type": "table",
                    "grid": [["Header1", "Header2"], ["Value1", "Value2"]],
                    "caption": "Sample Table",
                    "breadcrumb": "Document > Section > Tables",
                    "prov": {
                        "page_no": 2,
                        "bbox": {"l": 50, "t": 200, "r": 550, "b": 300}
                    },
                    "self_ref": "#/tables/0"
                },
                # Image element
                {
                    "type": "picture",
                    "caption": "Sample Image",
                    "breadcrumb": "Document > Section > Images",
                    "context_before": "Text before the image.",
                    "ocr_text": "Text extracted from image via OCR",
                    "context_after": "Text after the image.",
                    "external_path": "/path/to/images/test_image.png",
                    "mimetype": "image/png",
                    "width": 400,
                    "height": 300,
                    "prov": {
                        "page_no": 3,
                        "bbox": {"l": 100, "t": 150, "r": 500, "b": 450}
                    },
                    "self_ref": "#/pictures/0"
                }
            ]
        }

    def test_process_docling_json_to_sql_format(self):
        """Test the main processing function."""
        # Call the function with sample data
        result = process_docling_json_to_sql_format(self.sample_document, "test-doc-001")
        
        # Verify the overall structure
        self.assertIn("chunks", result)
        self.assertIn("furniture", result)
        self.assertIn("source_metadata", result)
        
        # Verify the source metadata
        self.assertEqual(result["source_metadata"]["filename"], "test_document.pdf")
        self.assertEqual(result["source_metadata"]["mimetype"], "application/pdf")
        self.assertEqual(result["source_metadata"]["binary_hash"], "abc123")
        
        # Verify furniture items
        self.assertEqual(len(result["furniture"]), 3)
        self.assertIn("Header Text", result["furniture"])
        self.assertIn("Footer Text", result["furniture"])
        self.assertIn("Page Number", result["furniture"])
        
        # Verify chunks
        self.assertEqual(len(result["chunks"]), 3)
        
        # Check if all required fields are present in each chunk
        required_fields = [
            "_id", "block_id", "doc_id", "content_type", "file_type", 
            "master_index", "master_index2", "coords_x", "coords_y", 
            "coords_cx", "coords_cy", "author_or_speaker", "added_to_collection", 
            "file_source", "table_block", "modified_date", "created_date", 
            "creator_tool", "external_files", "text_block", "header_text", 
            "text_search", "user_tags", "special_field1", "special_field2", 
            "special_field3", "graph_status", "dialog", "embedding_flags", "metadata"
        ]
        
        for chunk in result["chunks"]:
            for field in required_fields:
                self.assertIn(field, chunk)
    
    def test_text_chunk_processing(self):
        """Test processing of text chunks."""
        result = process_docling_json_to_sql_format(self.sample_document)
        
        # Get the first chunk (text chunk)
        text_chunk = result["chunks"][0]
        
        # Verify content type
        self.assertEqual(text_chunk["content_type"], "text")
        
        # Verify text content
        self.assertIn("This is a sample text paragraph.", text_chunk["text_block"])
        
        # Verify breadcrumb
        self.assertEqual(text_chunk["header_text"], "Document > Section > Subsection")
        
        # Verify coordinates
        self.assertEqual(text_chunk["coords_x"], 50)
        self.assertEqual(text_chunk["coords_y"], 100)
        self.assertEqual(text_chunk["coords_cx"], 500)  # 550 - 50
        self.assertEqual(text_chunk["coords_cy"], 50)   # 150 - 100
        
        # Verify metadata
        self.assertEqual(text_chunk["metadata"]["page_no"], 1)
        self.assertEqual(text_chunk["metadata"]["docling_label"], "text")
    
    def test_table_chunk_processing(self):
        """Test processing of table chunks."""
        result = process_docling_json_to_sql_format(self.sample_document)
        
        # Get the second chunk (table chunk)
        table_chunk = result["chunks"][1]
        
        # Verify content type
        self.assertEqual(table_chunk["content_type"], "table")
        
        # Verify table content
        self.assertIsNotNone(table_chunk["table_block"])
        
        # Parse table_block and verify content
        table_data = json.loads(table_chunk["table_block"])
        self.assertEqual(table_data, [["Header1", "Header2"], ["Value1", "Value2"]])
        
        # Verify text block contains caption
        self.assertIn("Sample Table", table_chunk["text_block"])
        
        # Verify metadata
        self.assertEqual(table_chunk["metadata"]["page_no"], 2)
        self.assertEqual(table_chunk["metadata"]["caption"], "Sample Table")
    
    def test_image_chunk_processing(self):
        """Test processing of image chunks."""
        result = process_docling_json_to_sql_format(self.sample_document)
        
        # Get the third chunk (image chunk)
        image_chunk = result["chunks"][2]
        
        # Verify content type
        self.assertEqual(image_chunk["content_type"], "image")
        
        # Verify external file path
        self.assertEqual(image_chunk["external_files"], "/path/to/images/test_image.png")
        
        # Verify text block contains OCR text
        self.assertIn("[Image Text: Text extracted from image via OCR]", image_chunk["text_block"])
        self.assertIn("Text before the image.", image_chunk["text_block"])
        self.assertIn("Text after the image.", image_chunk["text_block"])
        
        # Verify metadata
        self.assertEqual(image_chunk["metadata"]["page_no"], 3)
        self.assertEqual(image_chunk["metadata"]["caption"], "Sample Image")
        self.assertEqual(image_chunk["metadata"]["image_width"], 400)
        self.assertEqual(image_chunk["metadata"]["image_height"], 300)
        self.assertEqual(image_chunk["metadata"]["image_mimetype"], "image/png")
        self.assertEqual(image_chunk["metadata"]["image_ocr_text"], "Text extracted from image via OCR")
    
    def test_doc_id_assignment(self):
        """Test document ID assignment."""
        # Test with doc_id provided
        result_with_id = process_docling_json_to_sql_format(self.sample_document, "test-doc-123")
        for chunk in result_with_id["chunks"]:
            self.assertEqual(chunk["doc_id"], "test-doc-123")
        
        # Test without doc_id
        result_without_id = process_docling_json_to_sql_format(self.sample_document)
        for chunk in result_without_id["chunks"]:
            self.assertIsNone(chunk["doc_id"])
    

if __name__ == "__main__":
    unittest.main() 