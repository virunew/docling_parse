"""
Test module for CSV output formatting with special characters.

This module contains tests specifically for ensuring the CSV formatter 
correctly handles special characters such as quotes, commas, and newlines.
"""

import csv
import os
import tempfile
import unittest
from pathlib import Path
import sys
import io

# Add src directory to path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from output_formatter import OutputFormatter

class TestCsvSpecialCharsFormatter(unittest.TestCase):
    """Test cases specifically for CSV output formatting of special characters."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample document for testing with special characters
        self.test_document_special_chars = {
            "name": "test_document_special_chars",
            "metadata": {
                "title": "Test Document with \"Special\" Characters",
                "author": "Test, Author",
                "created": "2023-01-01"
            },
            "flattened_sequence": [
                {
                    "metadata": {"type": "heading", "page_number": 1},
                    "text": "Test Heading with \"Quotes\""
                },
                {
                    "metadata": {"type": "paragraph", "page_number": 1},
                    "text": "This is a paragraph with commas, quotes \"like this\", and multiple\nlines."
                },
                {
                    "metadata": {"type": "table", "page_number": 1, "caption": "Test Table, with \"Special\" Characters"},
                    "cells": [
                        {"row": 0, "col": 0, "text": "Header, 1", "rowspan": 1, "colspan": 1},
                        {"row": 0, "col": 1, "text": "Header \"2\"", "rowspan": 1, "colspan": 1},
                        {"row": 1, "col": 0, "text": "Data, 1\nSecond line", "rowspan": 1, "colspan": 1},
                        {"row": 1, "col": 1, "text": "Data \"2\"", "rowspan": 1, "colspan": 1}
                    ]
                }
            ]
        }
        
        # Create a formatter with default config
        self.formatter = OutputFormatter()
        
        # Create a temporary directory for output files
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_csv_escaping_quotes(self):
        """Test that quotes in CSV content are properly escaped."""
        # Format as CSV
        result = self.formatter.format_as_csv(self.test_document_special_chars)
        
        # CSV should be returned as a string
        self.assertIsInstance(result, str)
        
        # Parse the CSV content using csv module to verify it's valid
        csv_reader = csv.reader(io.StringIO(result))
        rows = list(csv_reader)
        
        # Heading with quotes should be properly escaped
        heading_row = next((row for row in rows if row[0] == "heading"), None)
        self.assertIsNotNone(heading_row)
        self.assertEqual(heading_row[2], 'Test Heading with "Quotes"')
        
        # Paragraph with quotes, commas and newlines should be properly handled
        paragraph_row = next((row for row in rows if row[0] == "paragraph"), None)
        self.assertIsNotNone(paragraph_row)
        self.assertTrue('quotes "like this"' in paragraph_row[2])
        self.assertTrue('commas' in paragraph_row[2])
        self.assertFalse('\n' in paragraph_row[2])  # Newlines should be replaced
        
        # Table cells with special chars should be properly escaped
        table_cell_rows = [row for row in rows if row[0] == "table_cell"]
        self.assertEqual(len(table_cell_rows), 4)  # Should have 4 cells
        
        # Check specific cells with special characters
        header1_cell = next((cell for cell in table_cell_rows if "Header, 1" in cell[2]), None)
        self.assertIsNotNone(header1_cell)
        
        header2_cell = next((cell for cell in table_cell_rows if 'Header "2"' in cell[2]), None)
        self.assertIsNotNone(header2_cell)
        
        data1_cell = next((cell for cell in table_cell_rows if "Data, 1" in cell[2]), None)
        self.assertIsNotNone(data1_cell)
        self.assertFalse('\n' in data1_cell[2])  # Newlines should be replaced
        
        data2_cell = next((cell for cell in table_cell_rows if 'Data "2"' in cell[2]), None)
        self.assertIsNotNone(data2_cell)
    
    def test_save_csv_with_special_chars(self):
        """Test saving CSV with special characters to a file."""
        # Define output path
        output_path = Path(self.temp_dir.name)
        
        # Save as CSV
        output_file = self.formatter.save_formatted_output(
            self.test_document_special_chars, output_path, "csv"
        )
        
        # Check that file was created
        self.assertTrue(output_file.exists())
        
        # Check file extension
        self.assertEqual(output_file.suffix, ".csv")
        
        # Read the file and verify it can be parsed as valid CSV
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Try to parse with csv.reader (will raise exception if invalid)
            csv_reader = csv.reader(io.StringIO(content))
            rows = list(csv_reader)
            
            # Basic validation of structure
            self.assertTrue(len(rows) > 1)
            self.assertEqual(rows[0], ["content_type", "page_number", "content", "level", "metadata"])

if __name__ == '__main__':
    unittest.main() 