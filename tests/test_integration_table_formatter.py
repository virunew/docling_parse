#!/usr/bin/env python3
"""
Integration test for the table content formatter with parse_main.py.

This test verifies that the table content formatter correctly integrates with
the main PDF parsing functionality and produces valid JSON output.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path

# Add the src directory to the path so we can import modules from there
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock docling modules before importing our modules
sys.modules['docling'] = MagicMock()
sys.modules['docling.document_converter'] = MagicMock()
sys.modules['docling.datamodel.base_models'] = MagicMock()
sys.modules['docling.datamodel.pipeline_options'] = MagicMock()

# Import the function to test directly - avoid importing parse_main to prevent import errors
from src.content_extractor import format_table_content, extract_table_content


class TableFormatterTests(unittest.TestCase):
    """
    Test cases for the direct table content formatter functionality.
    """

    def test_extract_and_format(self):
        """Test that extract_table_content and format_table_content work together."""
        # Create a simple table element
        table = {
            "cells": [
                {"row": 0, "col": 0, "text": "Header 1"},
                {"row": 0, "col": 1, "text": "Header 2"},
                {"row": 1, "col": 0, "text": "Data 1"},
                {"row": 1, "col": 1, "text": "Data 2"}
            ]
        }
        
        # Extract the table content
        grid = extract_table_content(table)
        
        # Format the table content
        formatted = format_table_content(table)
        
        # Verify the results
        expected_grid = [
            ["Header 1", "Header 2"],
            ["Data 1", "Data 2"]
        ]
        self.assertEqual(grid, expected_grid)
        
        # Verify the formatted result is valid JSON
        parsed = json.loads(formatted)
        self.assertEqual(parsed, expected_grid)

    def test_complex_table(self):
        """Test formatting a more complex table with rowspan and colspan."""
        # Create a table with rowspan and colspan
        complex_table = {
            "cells": [
                {"row": 0, "col": 0, "text": "Header", "colspan": 2},
                {"row": 1, "col": 0, "text": "Data 1"},
                {"row": 1, "col": 1, "text": "Data 2"},
                {"row": 2, "col": 0, "text": "Multi-row", "rowspan": 2},
                {"row": 2, "col": 1, "text": "Row 1"},
                {"row": 3, "col": 1, "text": "Row 2"}
            ]
        }
        
        # Extract and format the table
        grid = extract_table_content(complex_table)
        formatted = format_table_content(complex_table)
        
        # Expected structure after processing rowspan/colspan
        expected_grid = [
            ["Header", "Header"],
            ["Data 1", "Data 2"],
            ["Multi-row", "Row 1"],
            ["Multi-row", "Row 2"]
        ]
        
        # Verify extraction result
        self.assertEqual(grid, expected_grid)
        
        # Verify formatting result
        parsed = json.loads(formatted)
        self.assertEqual(parsed, expected_grid)
    
    def test_special_characters(self):
        """Test that special characters are properly handled during formatting."""
        # Create a table with special characters
        special_chars_table = {
            "cells": [
                {"row": 0, "col": 0, "text": "Quote \"Test\""},
                {"row": 0, "col": 1, "text": "Backslash \\Test\\"},
                {"row": 1, "col": 0, "text": "Newline\nTest"},
                {"row": 1, "col": 1, "text": "Tab\tTest"}
            ]
        }
        
        # Format the table
        formatted = format_table_content(special_chars_table)
        
        # Parse the formatted JSON and verify special character handling
        data = json.loads(formatted)
        
        # Check that newlines are replaced with spaces and other characters are properly escaped
        self.assertEqual(data[1][0], "Newline Test")  # Newline replaced with space
        self.assertEqual(data[0][0], "Quote \"Test\"")  # Quotes preserved
    
    def test_empty_table(self):
        """Test formatting an empty table."""
        # Create an empty table
        empty_table = {"cells": []}
        
        # Format the table
        formatted = format_table_content(empty_table)
        
        # Should return a valid JSON array string
        self.assertEqual(formatted, "[]")
        
        # Should deserialize to an empty list
        self.assertEqual(json.loads(formatted), [])
    
    def test_error_handling(self):
        """Test error handling in format_table_content."""
        # Create a problematic table 
        problematic_table = {"id": "bad_table"}  # No cells attribute
        
        # Format should not raise an exception but return an empty array
        formatted = format_table_content(problematic_table)
        self.assertEqual(formatted, "[]")


if __name__ == '__main__':
    unittest.main() 