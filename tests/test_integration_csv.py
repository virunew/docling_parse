"""
Integration test for CSV output format functionality.

This test verifies that the CSV export functionality works correctly 
with the OutputFormatter class.
"""

import os
import sys
import csv
import io
import unittest
import tempfile
import json
from pathlib import Path
import logging

# Configure logging to avoid output during tests
logging.basicConfig(level=logging.ERROR)

# Add src directory to path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the output formatter directly - avoids docling dependencies
from output_formatter import OutputFormatter

class TestCsvIntegration(unittest.TestCase):
    """Integration tests for CSV output format."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Create a mock document structure
        self.test_document = {
            "name": "test_integration",
            "metadata": {
                "title": "Test Integration Document",
                "author": "Test Author",
                "created": "2023-01-01"
            },
            "pages": [
                {
                    "page_number": 1,
                    "segments": [
                        {"text": "This is a heading", "metadata": {"type": "heading"}},
                        {"text": "This is a paragraph on page 1.", "metadata": {"type": "paragraph"}}
                    ],
                    "tables": [
                        {
                            "cells": [
                                {"row": 0, "col": 0, "text": "Header 1", "rowspan": 1, "colspan": 1},
                                {"row": 0, "col": 1, "text": "Header 2", "rowspan": 1, "colspan": 1},
                                {"row": 1, "col": 0, "text": "Data 1", "rowspan": 1, "colspan": 1},
                                {"row": 1, "col": 1, "text": "Data 2", "rowspan": 1, "colspan": 1}
                            ],
                            "metadata": {
                                "caption": "Test Table",
                                "page_number": 1
                            }
                        }
                    ]
                }
            ]
        }
        
        # Save mock document to a JSON file
        self.json_path = self.output_dir / "test_integration.json"
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_document, f)
        
        # Create formatter configuration
        self.formatter_config = {
            'include_metadata': True,
            'include_images': True,
            'image_base_url': '',
            'include_page_breaks': True,
            'include_captions': True
        }
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up temp directory
        self.temp_dir.cleanup()
    
    def test_csv_output_format(self):
        """Test that CSV output formatting works correctly."""
        # Create the formatter with our config
        formatter = OutputFormatter(self.formatter_config)
        
        # Format as CSV
        csv_content = formatter.format_as_csv(self.test_document)
        
        # Verify it's a string
        self.assertIsInstance(csv_content, str)
        
        # Save to a file using the formatter's save method
        output_file = formatter.save_formatted_output(
            self.test_document,
            self.output_dir,
            "csv"
        )
        
        # Verify file was created with correct extension
        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.suffix, ".csv")
        
        # Read the CSV file and verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Parse CSV
            csv_reader = csv.reader(io.StringIO(content))
            rows = list(csv_reader)
            
            # Basic validations
            self.assertTrue(len(rows) > 1, "CSV should have at least header and one row")
            self.assertEqual(rows[0], ["content_type", "page_number", "content", "level", "metadata"])
            
            # Count rows by type
            content_types = {}
            for row in rows[1:]:  # Skip header
                content_type = row[0]
                content_types[content_type] = content_types.get(content_type, 0) + 1
            
            # Verify counts match expected content
            self.assertIn("paragraph", content_types, "CSV should contain paragraph entries")
            self.assertIn("table", content_types, "CSV should contain table entries")
            self.assertIn("table_cell", content_types, "CSV should contain table_cell entries")
            
            # Specifically check for table cells
            self.assertEqual(content_types.get("table_cell", 0), 4, "Should have 4 table cells")
    
    def test_csv_output_with_special_chars(self):
        """Test CSV output with special characters."""
        # Create document with special characters
        document_with_special_chars = {
            "name": "test_special_chars",
            "metadata": {
                "title": "Test Document with \"Special\" Characters",
                "author": "Test, Author"
            },
            "flattened_sequence": [
                {
                    "metadata": {"type": "heading", "page_number": 1},
                    "text": "Test Heading with \"Quotes\""
                },
                {
                    "metadata": {"type": "paragraph", "page_number": 1},
                    "text": "This is a paragraph with commas, quotes \"like this\", and multiple\nlines."
                }
            ]
        }
        
        # Create the formatter
        formatter = OutputFormatter(self.formatter_config)
        
        # Format and save
        output_file = formatter.save_formatted_output(
            document_with_special_chars,
            self.output_dir,
            "csv"
        )
        
        # Read and verify
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # This should parse without errors if quotes and commas are properly escaped
            csv_reader = csv.reader(io.StringIO(content))
            rows = list(csv_reader)
            
            # Find the paragraph row
            paragraph_row = next((row for row in rows if row[0] == "paragraph"), None)
            self.assertIsNotNone(paragraph_row)
            
            # Verify special characters
            self.assertTrue("commas" in paragraph_row[2])
            self.assertTrue("quotes" in paragraph_row[2])
            self.assertFalse("\n" in paragraph_row[2])  # Newlines should be replaced
    
    def test_multiple_formats(self):
        """Test that the same document can be exported to multiple formats."""
        formatter = OutputFormatter(self.formatter_config)
        
        # Format and save as CSV
        csv_file = formatter.save_formatted_output(
            self.test_document,
            self.output_dir,
            "csv"
        )
        
        # Format and save as JSON
        json_file = formatter.save_formatted_output(
            self.test_document,
            self.output_dir,
            "json"
        )
        
        # Verify both files exist
        self.assertTrue(csv_file.exists())
        self.assertEqual(csv_file.suffix, ".csv")
        
        self.assertTrue(json_file.exists())
        self.assertEqual(json_file.suffix, ".json")
        
        # Verify CSV content
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_content = f.read()
            csv_reader = csv.reader(io.StringIO(csv_content))
            rows = list(csv_reader)
            self.assertTrue(len(rows) > 1)
        
        # Verify JSON content
        with open(json_file, 'r', encoding='utf-8') as f:
            json_content = json.load(f)
            self.assertIn("metadata", json_content)
            self.assertIn("content", json_content)

if __name__ == '__main__':
    unittest.main() 