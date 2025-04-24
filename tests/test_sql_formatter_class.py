"""
Test cases for the SQLFormatter class.

This module tests the functionality of the SQLFormatter class, which converts
Docling document data into a standardized SQL-compatible JSON format.
"""
import json
import os
import sys
import unittest
import tempfile
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the class to test
from src.sql_formatter import SQLFormatter


class TestSQLFormatterClass(unittest.TestCase):
    """Test cases for the SQLFormatter class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create an instance of the SQLFormatter
        self.formatter = SQLFormatter()
        
        # Create a temporary directory for output files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a sample document data dictionary for testing
        self.sample_document = {
            "name": "test_document",
            "metadata": {
                "filename": "test_document.pdf",
                "mimetype": "application/pdf",
                "binary_hash": "abc123"
            },
            "furniture": [
                {"text": "Header Text", "type": "header"},
                {"text": "Footer Text", "type": "footer"}
            ],
            "body": [
                # Text element
                {
                    "type": "text",
                    "text": "This is a sample text paragraph.",
                    "breadcrumb": "Section 1",
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
                    "breadcrumb": "Section 2",
                    "prov": {
                        "page_no": 2,
                        "bbox": {"l": 50, "t": 200, "r": 550, "b": 300}
                    },
                    "self_ref": "#/tables/0"
                }
            ],
            "element_map": {
                "flattened_sequence": [
                    # Text element
                    {
                        "type": "text",
                        "text_content": "This is a sample text paragraph.",
                        "content_layer": "content",
                        "extracted_metadata": {
                            "breadcrumb": "Section 1",
                            "page_no": 1,
                            "bbox_raw": {"l": 50, "t": 100, "r": 550, "b": 150}
                        }
                    },
                    # Table element
                    {
                        "type": "table",
                        "content_layer": "content",
                        "table_content": [["Header1", "Header2"], ["Value1", "Value2"]],
                        "extracted_metadata": {
                            "breadcrumb": "Section 2",
                            "page_no": 2,
                            "bbox_raw": {"l": 50, "t": 200, "r": 550, "b": 300},
                            "caption": "Sample Table"
                        }
                    }
                ]
            }
        }
        
        # Create a sample PDF path
        self.sample_pdf_path = os.path.join(self.temp_dir.name, "test_document.pdf")

    def tearDown(self):
        """Clean up temporary resources."""
        self.temp_dir.cleanup()

    def test_format_as_sql(self):
        """Test the format_as_sql method."""
        # Call the format_as_sql method
        result = self.formatter.format_as_sql(self.sample_document, "test-123")
        
        # Verify the result structure
        self.assertIn("chunks", result)
        self.assertIn("furniture", result)
        self.assertIn("source_metadata", result)
        
        # Verify the source metadata
        self.assertEqual(result["source_metadata"]["filename"], "test_document.pdf")
        self.assertEqual(result["source_metadata"]["mimetype"], "application/pdf")
        
        # Verify furniture items are included
        self.assertEqual(len(result["furniture"]), 2)
        self.assertIn("Header Text", result["furniture"])
        self.assertIn("Footer Text", result["furniture"])
        
        # Verify chunks are created correctly
        self.assertEqual(len(result["chunks"]), 2)
        
        # Check if doc_id is properly set for all chunks
        for chunk in result["chunks"]:
            self.assertEqual(chunk["doc_id"], "test-123")
    
    def test_save_formatted_output(self):
        """Test the save_formatted_output method."""
        # Call the method
        output_file = self.formatter.save_formatted_output(
            self.sample_document, 
            self.temp_dir.name
        )
        
        # Verify the output file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Verify the output file name
        self.assertTrue(output_file.endswith("test_document_sql.json"))
        
        # Read the output file and verify its structure
        with open(output_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        # Verify the result structure
        self.assertIn("chunks", result)
        self.assertIn("furniture", result)
        self.assertIn("source_metadata", result)
        
        # Verify the source metadata
        self.assertEqual(result["source_metadata"]["filename"], "test_document.pdf")
        
        # Verify chunks are created correctly
        self.assertEqual(len(result["chunks"]), 2)
    
    def test_save_formatted_output_with_standardized_format(self):
        """Test the save_formatted_output method with standardized format."""
        # Call the method with use_standardized_format=True
        output_file = self.formatter.save_formatted_output(
            self.sample_document, 
            self.temp_dir.name,
            use_standardized_format=True,
            pdf_path=self.sample_pdf_path
        )
        
        # Verify the output file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Verify the output file name
        self.assertTrue(output_file.endswith("_standardized.json"))
        
        # Read the output file and verify its structure
        with open(output_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        # Verify the result structure
        self.assertIn("chunks", result)
        self.assertIn("furniture", result)
        self.assertIn("source_metadata", result)
    
    def test_save_formatted_output_with_standardized_format_missing_pdf_path(self):
        """Test the save_formatted_output method with standardized format but missing PDF path."""
        # Call the method with use_standardized_format=True but no pdf_path
        output_file = self.formatter.save_formatted_output(
            self.sample_document, 
            self.temp_dir.name,
            use_standardized_format=True
        )
        
        # Should fall back to default SQL format
        self.assertTrue(output_file.endswith("_sql.json"))
    
    def test_error_handling(self):
        """Test error handling in the format_as_sql method."""
        # Create an invalid document (missing required fields)
        invalid_document = {"invalid": "data"}
        
        # Call the method - it should not raise an exception
        result = self.formatter.format_as_sql(invalid_document)
        
        # Verify the result is a valid minimal structure
        self.assertIn("chunks", result)
        self.assertIn("furniture", result)
        self.assertIn("source_metadata", result)
        
        # Verify chunks and furniture are empty since we couldn't process anything
        self.assertEqual(len(result["chunks"]), 0)
        self.assertEqual(len(result["furniture"]), 0)


if __name__ == "__main__":
    unittest.main() 