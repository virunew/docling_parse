#!/usr/bin/env python3
"""
Tests for the standardized output generation functionality.

This module tests the `save_standardized_output` function to ensure that it correctly
formats document data into the required structure with top-level keys:
- chunks: List of content elements
- furniture: List of non-content elements
- source_metadata: Metadata about the source document
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

# Import the function to test
from format_standardized_output import save_standardized_output


class TestStandardizedOutput(unittest.TestCase):
    """Test cases for the standardized output generation."""

    def setUp(self):
        """Set up test environment with sample document data."""
        # Create a temporary directory for output
        self.output_dir = tempfile.mkdtemp()
        
        # Sample document data similar to what would come from parse_main.py
        self.sample_document = {
            "elements": [
                {
                    "self_ref": "#/texts/0",
                    "type": "text",
                    "content": "This is a sample text",
                    "content_layer": "main",
                    "page_no": 1,
                    "bbox": {"l": 100, "t": 100, "r": 300, "b": 150},
                    "breadcrumb": "Document > Section"
                },
                {
                    "self_ref": "#/texts/1",
                    "type": "text",
                    "content": "This is a header",
                    "content_layer": "furniture",
                    "page_no": 1,
                    "bbox": {"l": 50, "t": 50, "r": 250, "b": 70}
                },
                {
                    "self_ref": "#/pictures/0",
                    "type": "picture",
                    "content_layer": "main",
                    "image_path": "/path/to/image.png",
                    "mimetype": "image/png",
                    "width": 400,
                    "height": 300,
                    "page_no": 1,
                    "bbox": {"l": 150, "t": 200, "r": 550, "b": 500},
                    "ocr_text": "Text extracted from image",
                    "preceding_text": "Text before image",
                    "succeeding_text": "Text after image",
                    "breadcrumb": "Document > Section"
                },
                {
                    "self_ref": "#/tables/0",
                    "type": "table",
                    "content_layer": "main",
                    "data": [["Header 1", "Header 2"], ["Cell 1", "Cell 2"]],
                    "page_no": 2,
                    "bbox": {"l": 100, "t": 300, "r": 500, "b": 400},
                    "breadcrumb": "Document > Section > Subsection"
                }
            ],
            "metadata": {
                "title": "Sample Document",
                "author": "Test Author",
                "date": "2023-01-01"
            }
        }
        
        # Path to a dummy PDF file for testing
        self.pdf_path = os.path.join(self.output_dir, "sample.pdf")
        # Create an empty file
        Path(self.pdf_path).touch()

    def test_standardized_output_structure(self):
        """Test that the standardized output has the correct structure with required top-level keys."""
        # Call the function being tested
        output_path = save_standardized_output(self.sample_document, self.output_dir, self.pdf_path)
        
        # Check that the output file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Load the output file
        with open(output_path, 'r', encoding='utf-8') as f:
            output_data = json.load(f)
        
        # Check that the output has the required top-level keys
        self.assertIn("chunks", output_data)
        self.assertIn("furniture", output_data)
        self.assertIn("source_metadata", output_data)
        
        # Check that chunks, furniture, and source_metadata have the correct types
        self.assertIsInstance(output_data["chunks"], list)
        self.assertIsInstance(output_data["furniture"], list)
        self.assertIsInstance(output_data["source_metadata"], dict)
        
        # Check that the number of chunks is correct (3 main content elements)
        self.assertEqual(len(output_data["chunks"]), 3)
        
        # Check that the number of furniture items is correct (1 furniture element)
        self.assertEqual(len(output_data["furniture"]), 1)
        
        # Check that the source_metadata contains the correct information
        self.assertEqual(output_data["source_metadata"]["filename"], "sample.pdf")
        self.assertEqual(output_data["source_metadata"]["mimetype"], "application/pdf")
        self.assertEqual(output_data["source_metadata"]["title"], "Sample Document")
        self.assertEqual(output_data["source_metadata"]["author"], "Test Author")
        self.assertEqual(output_data["source_metadata"]["date"], "2023-01-01")
    
    def test_chunk_fields(self):
        """Test that chunks have all the required fields as specified in the PRD."""
        # Call the function being tested
        output_path = save_standardized_output(self.sample_document, self.output_dir, self.pdf_path)
        
        # Load the output file
        with open(output_path, 'r', encoding='utf-8') as f:
            output_data = json.load(f)
        
        # Get the first chunk for testing
        chunk = output_data["chunks"][0]
        
        # Check that the chunk has all the required fields
        required_fields = [
            "_id", "block_id", "doc_id", "content_type", "file_type",
            "master_index", "master_index2", "coords_x", "coords_y",
            "coords_cx", "coords_cy", "author_or_speaker", "added_to_collection",
            "file_source", "table_block", "modified_date", "created_date",
            "creator_tool", "external_files", "text_block", "header_text",
            "text_search", "user_tags", "special_field1", "special_field2",
            "special_field3", "graph_status", "dialog", "embedding_flags"
        ]
        
        for field in required_fields:
            self.assertIn(field, chunk)
        
        # Check that the creator_tool field is set correctly
        self.assertEqual(chunk["creator_tool"], "DoclingToJsonScript_V1.1")
        
        # Check that the content type is set correctly
        self.assertEqual(chunk["content_type"], "text")
        
        # Check that the text block contains the breadcrumb and content
        self.assertIn("Document > Section", chunk["text_block"])
        self.assertIn("This is a sample text", chunk["text_block"])
        
        # Check that the header_text is set to the breadcrumb
        self.assertEqual(chunk["header_text"], "Document > Section")
        self.assertEqual(chunk["special_field2"], "Document > Section")
    
    def test_different_content_types(self):
        """Test that different content types (text, table, image) are processed correctly."""
        # Call the function being tested
        output_path = save_standardized_output(self.sample_document, self.output_dir, self.pdf_path)
        
        # Load the output file
        with open(output_path, 'r', encoding='utf-8') as f:
            output_data = json.load(f)
        
        # Find chunks by content_type
        text_chunks = [c for c in output_data["chunks"] if c["content_type"] == "text"]
        table_chunks = [c for c in output_data["chunks"] if c["content_type"] == "table"]
        image_chunks = [c for c in output_data["chunks"] if c["content_type"] == "image"]
        
        # Check that there's at least one of each type
        self.assertGreaterEqual(len(text_chunks), 1)
        self.assertGreaterEqual(len(table_chunks), 1)
        self.assertGreaterEqual(len(image_chunks), 1)
        
        # Check table chunk has table_block field
        table_chunk = table_chunks[0]
        self.assertIsNotNone(table_chunk["table_block"])
        
        # Check that the table_block can be parsed as JSON and has the expected structure
        table_data = json.loads(table_chunk["table_block"])
        self.assertEqual(len(table_data), 2)  # 2 rows
        self.assertEqual(len(table_data[0]), 2)  # 2 columns
        self.assertEqual(table_data[0][0], "Header 1")
        
        # Check image chunk has external_files field
        image_chunk = image_chunks[0]
        self.assertEqual(image_chunk["external_files"], "/path/to/image.png")
        
        # Check that the text_block for the image includes the OCR text and surrounding text
        self.assertIn("[Image Text: Text extracted from image]", image_chunk["text_block"])
        self.assertIn("Text before image", image_chunk["text_block"])
        self.assertIn("Text after image", image_chunk["text_block"])

    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary output file
        output_path = os.path.join(self.output_dir, "standardized_output.json")
        if os.path.exists(output_path):
            os.remove(output_path)
            
        # Remove the dummy PDF file
        if os.path.exists(self.pdf_path):
            os.remove(self.pdf_path)
            
        # Remove the temporary directory
        if os.path.exists(self.output_dir):
            os.rmdir(self.output_dir)


if __name__ == "__main__":
    unittest.main() 