#!/usr/bin/env python3
"""
Test for the table content formatter functionality.

This module tests the format_table_content function to ensure it correctly
formats table content as a JSON-serializable string.
"""

import json
import unittest
import sys
import os
from typing import Dict, Any, List

# Add the src directory to the path so we can import modules from there
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the function to test
from src.content_extractor import format_table_content, extract_table_content


class TableFormatterTests(unittest.TestCase):
    """
    Test cases for the table content formatter functionality.
    """

    def test_empty_table(self):
        """Test formatting an empty table."""
        empty_table = {"cells": []}
        result = format_table_content(empty_table)
        
        # Should return an empty JSON array string
        self.assertEqual(result, "[]")
        
        # Should be valid JSON and deserialize to an empty list
        self.assertEqual(json.loads(result), [])

    def test_simple_table(self):
        """Test formatting a simple table with basic content."""
        simple_table = {
            "cells": [
                {"row": 0, "col": 0, "text": "Header 1"},
                {"row": 0, "col": 1, "text": "Header 2"},
                {"row": 1, "col": 0, "text": "Data 1"},
                {"row": 1, "col": 1, "text": "Data 2"}
            ]
        }
        
        result = format_table_content(simple_table)
        
        # Should be valid JSON
        deserialized = json.loads(result)
        
        # Should match the expected structure
        expected = [
            ["Header 1", "Header 2"],
            ["Data 1", "Data 2"]
        ]
        self.assertEqual(deserialized, expected)

    def test_table_with_rowspan_colspan(self):
        """Test formatting a table with rowspan and colspan attributes."""
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
        
        result = format_table_content(complex_table)
        deserialized = json.loads(result)
        
        # Expected structure with rowspan/colspan applied
        expected = [
            ["Header", "Header"],
            ["Data 1", "Data 2"],
            ["Multi-row", "Row 1"],
            ["Multi-row", "Row 2"]
        ]
        self.assertEqual(deserialized, expected)

    def test_table_with_special_characters(self):
        """Test formatting a table with special characters that need proper JSON escaping."""
        special_chars_table = {
            "cells": [
                {"row": 0, "col": 0, "text": "Quote \"Test\""},
                {"row": 0, "col": 1, "text": "Backslash \\Test\\"},
                {"row": 1, "col": 0, "text": "Newline\nTest"},
                {"row": 1, "col": 1, "text": "Tab\tTest"}
            ]
        }
        
        result = format_table_content(special_chars_table)
        
        # Should be valid JSON
        try:
            deserialized = json.loads(result)
            self.assertTrue(True)  # If we reach here, JSON parsing was successful
        except json.JSONDecodeError:
            self.fail("format_table_content produced invalid JSON with special characters")
        
        # Check that newlines are replaced with spaces and other characters are properly escaped
        self.assertEqual(deserialized[1][0], "Newline Test")  # Newline replaced with space

    def test_extract_then_format(self):
        """Test extracting table content and then formatting it."""
        table = {
            "cells": [
                {"row": 0, "col": 0, "text": "Header 1"},
                {"row": 0, "col": 1, "text": "Header 2"},
                {"row": 1, "col": 0, "text": "Data 1"},
                {"row": 1, "col": 1, "text": "Data 2"}
            ]
        }
        
        # First extract the table content
        grid = extract_table_content(table)
        
        # Verify the extraction
        expected_grid = [
            ["Header 1", "Header 2"],
            ["Data 1", "Data 2"]
        ]
        self.assertEqual(grid, expected_grid)
        
        # Now format it and check the result
        result = format_table_content(table)
        deserialized = json.loads(result)
        self.assertEqual(deserialized, expected_grid)

    def test_error_handling(self):
        """Test that errors during formatting are handled gracefully."""
        # Create a table object that will cause an error when processed
        problematic_table = {"id": "bad_table"}  # Missing cells attribute
        
        # Should not raise an exception but return empty array
        result = format_table_content(problematic_table)
        self.assertEqual(result, "[]")


if __name__ == '__main__':
    unittest.main() 