"""
Test module specifically for CSV output formatting.

This module contains detailed tests for the CSV output formatter functionality.
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

class TestCsvOutputFormatter(unittest.TestCase):
    """Test cases specifically for CSV output functionality of OutputFormatter."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample document for testing
        self.test_document = {
            "name": "test_document",
            "metadata": {
                "title": "Test Document",
                "author": "Test Author",
                "created": "2023-01-01"
            },
            "pages": [
                {
                    "page_number": 1,
                    "segments": [
                        {"text": "This is a paragraph on page 1."},
                        {"text": "This is another paragraph on page 1."}
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
                    ],
                    "pictures": [
                        {
                            "image_path": "images/test_image.png",
                            "metadata": {
                                "caption": "Test Image",
                                "page_number": 1,
                                "width": 100,
                                "height": 100
                            }
                        }
                    ]
                },
                {
                    "page_number": 2,
                    "segments": [
                        {"text": "This is a paragraph on page 2."}
                    ]
                }
            ]
        }
        
        # Create a document with flattened sequence for testing
        self.test_document_with_sequence = {
            "name": "test_document_sequence",
            "metadata": {
                "title": "Test Document With Sequence",
                "author": "Test Author",
                "created": "2023-01-01"
            },
            "flattened_sequence": [
                {
                    "metadata": {"type": "heading", "page_number": 1},
                    "text": "Test Heading"
                },
                {
                    "metadata": {"type": "paragraph", "page_number": 1},
                    "text": "This is a paragraph in a sequence."
                },
                {
                    "metadata": {"type": "table", "page_number": 1, "caption": "Test Table"},
                    "cells": [
                        {"row": 0, "col": 0, "text": "Header 1", "rowspan": 1, "colspan": 1},
                        {"row": 0, "col": 1, "text": "Header 2", "rowspan": 1, "colspan": 1},
                        {"row": 1, "col": 0, "text": "Data 1", "rowspan": 1, "colspan": 1},
                        {"row": 1, "col": 1, "text": "Data 2", "rowspan": 1, "colspan": 1}
                    ]
                },
                {
                    "metadata": {"type": "paragraph", "page_number": 1},
                    "text": "Another paragraph."
                },
                {
                    "metadata": {"type": "image", "page_number": 1, "caption": "Test Image"},
                    "image_path": "images/test_image.png"
                },
                {
                    "metadata": {"type": "heading", "page_number": 2},
                    "text": "Page 2 Heading"
                },
                {
                    "metadata": {"type": "paragraph", "page_number": 2},
                    "text": "This is a paragraph on page 2."
                }
            ]
        }
        
        # Create an empty document for testing
        self.empty_document = {
            "name": "empty_document",
            "metadata": {
                "title": "Empty Document"
            },
            "pages": []
        }
        
        # Create a formatter with default config
        self.formatter = OutputFormatter()
        
        # Create a temporary directory for output files
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_csv_format_with_pages(self):
        """Test CSV formatting with document using pages structure."""
        # Format as CSV
        result = self.formatter.format_as_csv(self.test_document)
        
        # CSV should be returned as a string
        self.assertIsInstance(result, str)
        
        # Parse the CSV content
        csv_reader = csv.reader(io.StringIO(result))
        rows = list(csv_reader)
        
        # Check header row
        self.assertEqual(rows[0], ["content_type", "page_number", "content", "level", "metadata"])
        
        # Count the content types
        content_types = [row[0] for row in rows[1:]]
        content_counts = {}
        for content_type in content_types:
            content_counts[content_type] = content_counts.get(content_type, 0) + 1
        
        # Verify counts - should match what we have in the test document
        self.assertEqual(content_counts.get("paragraph", 0), 3)  # 2 from page 1, 1 from page 2
        self.assertEqual(content_counts.get("table", 0), 1)
        self.assertEqual(content_counts.get("table_cell", 0), 4)  # 2x2 table
        self.assertEqual(content_counts.get("image", 0), 1)
        self.assertEqual(content_counts.get("page_break", 0), 1)  # Between pages 1 and 2
        
        # Check page numbers
        page_numbers = [row[1] for row in rows[1:]]
        self.assertTrue("1" in page_numbers)
        self.assertTrue("2" in page_numbers)
        
        # Check content values for paragraphs
        paragraph_contents = [row[2] for row in rows[1:] if row[0] == "paragraph"]
        self.assertTrue(any("This is a paragraph on page 1" in content for content in paragraph_contents))
        self.assertTrue(any("This is another paragraph on page 1" in content for content in paragraph_contents))
        self.assertTrue(any("This is a paragraph on page 2" in content for content in paragraph_contents))
        
        # Check table cell contents
        table_cell_contents = [row[2] for row in rows[1:] if row[0] == "table_cell"]
        self.assertTrue(any("Header 1" in content for content in table_cell_contents))
        self.assertTrue(any("Header 2" in content for content in table_cell_contents))
        self.assertTrue(any("Data 1" in content for content in table_cell_contents))
        self.assertTrue(any("Data 2" in content for content in table_cell_contents))
    
    def test_csv_format_with_sequence(self):
        """Test CSV formatting with document using flattened_sequence structure."""
        # Format as CSV
        result = self.formatter.format_as_csv(self.test_document_with_sequence)
        
        # Parse the CSV content
        csv_reader = csv.reader(io.StringIO(result))
        rows = list(csv_reader)
        
        # Check header row
        self.assertEqual(rows[0], ["content_type", "page_number", "content", "level", "metadata"])
        
        # Extract content types in order (should match expected sequence)
        content_types = [row[0] for row in rows[1:]]
        expected_types = ['heading', 'paragraph', 'table', 'table_cell', 'table_cell', 
                          'table_cell', 'table_cell', 'paragraph', 'image', 
                          'page_break', 'heading', 'paragraph']
        
        self.assertEqual(content_types, expected_types)
        
        # Check heading content
        heading_contents = [row[2] for row in rows[1:] if row[0] == "heading"]
        self.assertEqual(len(heading_contents), 2)
        # Check that the heading text is in there somewhere
        self.assertTrue("Test Heading" in heading_contents[0])
        self.assertTrue("Page 2 Heading" in heading_contents[1])
        
        # Check heading levels (should be 1 by default)
        heading_levels = [row[3] for row in rows[1:] if row[0] == "heading"]
        self.assertEqual(heading_levels, ["1", "1"])
    
    def test_csv_format_empty_document(self):
        """Test CSV formatting with an empty document."""
        # Format as CSV
        result = self.formatter.format_as_csv(self.empty_document)
        
        # CSV should be returned as a string
        self.assertIsInstance(result, str)
        
        # Parse the CSV content
        csv_reader = csv.reader(io.StringIO(result))
        rows = list(csv_reader)
        
        # Should have at least 2 rows: header and info row
        self.assertTrue(len(rows) >= 2)
        
        # Check header row
        self.assertEqual(rows[0], ["content_type", "page_number", "content", "level", "metadata"])
        
        # Check info row for empty document
        if len(rows) == 2 and rows[1][0] == "info":
            self.assertEqual(rows[1][0], "info")
            self.assertTrue("No content found" in rows[1][2])
    
    def test_save_formatted_output_csv(self):
        """Test saving formatted output as CSV."""
        # Define output path
        output_path = Path(self.temp_dir.name)
        
        # Save as CSV
        output_file = self.formatter.save_formatted_output(
            self.test_document, output_path, "csv"
        )
        
        # Check that file was created
        self.assertTrue(output_file.exists())
        
        # Check file extension
        self.assertEqual(output_file.suffix, ".csv")
        
        # Check file content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Verify header and content
            csv_reader = csv.reader(io.StringIO(content))
            rows = list(csv_reader)
            
            # Check header row
            self.assertEqual(rows[0], ["content_type", "page_number", "content", "level", "metadata"])
            
            # Count the content types
            content_types = [row[0] for row in rows[1:]]
            content_counts = {}
            for content_type in content_types:
                content_counts[content_type] = content_counts.get(content_type, 0) + 1
            
            # Verify counts - should match what we have in the test document
            self.assertEqual(content_counts.get("paragraph", 0), 3)  # 2 from page 1, 1 from page 2
            self.assertEqual(content_counts.get("table", 0), 1)
            self.assertEqual(content_counts.get("table_cell", 0), 4)  # 2x2 table
            self.assertEqual(content_counts.get("image", 0), 1)

if __name__ == '__main__':
    unittest.main() 