#!/usr/bin/env python3
"""
Test the CSV formatting functionality of the OutputFormatter class.
"""

import json
import os
import sys
import unittest
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from output_formatter import OutputFormatter


class TestOutputFormatterCSV(unittest.TestCase):
    """Test the CSV output functionality of OutputFormatter."""

    def setUp(self):
        """Set up the test case."""
        # Create an instance of OutputFormatter with default config
        self.formatter = OutputFormatter()
        
        # Base directory is the parent of the current directory (tests)
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Path to test data
        self.test_file = self.base_dir / 'output_main' / 'SBW_AI sample page10-11.json'
        
        # Ensure the test file exists
        self.assertTrue(self.test_file.exists(), f"Test file {self.test_file} does not exist")

    def test_format_as_csv(self):
        """Test that format_as_csv returns valid CSV data with correct headers and content."""
        # Load the test document
        with open(self.test_file, 'r', encoding='utf-8') as f:
            document_data = json.load(f)
        
        # Format as CSV
        csv_output = self.formatter.format_as_csv(document_data)
        
        # Basic validation
        self.assertIsInstance(csv_output, str, "CSV output should be a string")
        self.assertTrue(len(csv_output) > 0, "CSV output should not be empty")
        
        # Check for headers
        expected_headers = "content_type,page_number,content,level,metadata"
        self.assertTrue(csv_output.startswith(expected_headers), 
                        f"CSV should start with headers: {expected_headers}")
        
        # Check that it contains actual content (not just "No content found")
        self.assertNotIn("No content found in document", csv_output, 
                        "CSV should not contain 'No content found in document'")
        
        # Count the number of lines to make sure it's processing content
        lines = csv_output.strip().split('\n')
        self.assertGreater(len(lines), 1, "CSV should have more than just the header line")
        
        # Print the first few lines of output for debugging
        print("\nFirst 5 lines of CSV output:")
        for i, line in enumerate(lines[:5]):
            print(f"{i}: {line}")
        
        # Print content count
        print(f"Total lines in CSV: {len(lines)}")

    def test_save_formatted_output_csv(self):
        """Test the save_formatted_output method with CSV format."""
        # Load the test document
        with open(self.test_file, 'r', encoding='utf-8') as f:
            document_data = json.load(f)
        
        # Create a temporary output directory
        output_dir = self.base_dir / 'test_output'
        output_dir.mkdir(exist_ok=True)
        
        # Save as CSV
        output_file = self.formatter.save_formatted_output(
            document_data, 
            output_dir, 
            'csv'
        )
        
        # Verify the file exists
        self.assertTrue(output_file.exists(), f"Output file {output_file} should exist")
        
        # Check the content
        with open(output_file, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        # Validate the content
        self.assertTrue(len(csv_content) > 0, "CSV file should not be empty")
        self.assertTrue(csv_content.startswith("content_type,page_number,content,level,metadata"), 
                        "CSV should start with correct headers")
        self.assertNotIn("No content found in document", csv_content, 
                        "CSV should not contain 'No content found in document'")


if __name__ == '__main__':
    unittest.main() 