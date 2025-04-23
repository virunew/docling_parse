#!/usr/bin/env python3
"""
Integration tests for the OutputFormatter.

Tests the integration between parse_main.py and output_formatter.py,
particularly focusing on the CSV output format which previously had issues.
"""

import json
import os
import sys
import unittest
import shutil
import tempfile
import subprocess
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from output_formatter import OutputFormatter


class TestOutputFormatterIntegration(unittest.TestCase):
    """
    Integration tests for the OutputFormatter.
    
    These tests verify that the OutputFormatter correctly handles real document data
    and produces valid output files in all supported formats.
    """

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for output files
        self.test_output_dir = tempfile.mkdtemp()
        
        # Base directory is the parent of the current directory (tests)
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Path to test data
        self.test_file = self.base_dir / 'output_main' / 'SBW_AI sample page10-11.json'
        
        # Ensure the test file exists
        self.assertTrue(self.test_file.exists(), f"Test file {self.test_file} does not exist")
        
        # Create formatter instance with default configuration
        self.formatter = OutputFormatter()
        
        # Load test document data
        with open(self.test_file, 'r', encoding='utf-8') as f:
            self.document_data = json.load(f)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.test_output_dir)
    
    def test_parse_main_with_csv_output(self):
        """
        Test the end-to-end flow using parse_main.py with CSV output.
        
        This test runs the parse_main.py script with a real document and 
        verifies that it correctly generates a CSV file with proper content.
        """
        # Path to parse_main.py
        parse_main_script = self.base_dir / 'src' / 'parse_main.py'
        
        # Output directory for this test
        output_dir = Path(self.test_output_dir) / 'csv_test'
        
        # Run the parse_main.py script
        cmd = [
            sys.executable,
            str(parse_main_script),
            f"--pdf_path={self.test_file}",
            f"--output_dir={output_dir}",
            "--output_format=csv"
        ]
        
        process = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False
        )
        
        # Check process output for error messages
        if process.returncode != 0:
            print(f"Command failed with return code {process.returncode}")
            print(f"STDOUT: {process.stdout}")
            print(f"STDERR: {process.stderr}")
        
        # Verify the process completed successfully
        self.assertEqual(process.returncode, 0, "parse_main.py script failed")
        
        # Check that the CSV file was created
        expected_csv_file = output_dir / 'SBW_AI sample page10-11.csv'
        self.assertTrue(expected_csv_file.exists(), f"CSV file {expected_csv_file} was not created")
        
        # Read the CSV file content
        with open(expected_csv_file, 'r', encoding='utf-8') as f:
            csv_content = f.read()
            
        # Verify basic content
        self.assertTrue(len(csv_content) > 0, "CSV file should not be empty")
        self.assertTrue(csv_content.startswith("content_type,page_number,content,level,metadata"), 
                       "CSV should start with expected headers")
        self.assertNotIn("No content found in document", csv_content, 
                        "CSV should not contain 'No content found in document'")
        
        # Count lines to verify it's processing text content
        lines = csv_content.split('\n')
        self.assertGreater(len(lines), 10, "CSV should have substantial content")
        
        # Check for expected content types
        content_types = [line.split(',')[0] for line in lines if line and line[0] != 'c']  # Skip header
        self.assertIn("heading", content_types, "CSV should include heading content")
        self.assertIn("paragraph", content_types, "CSV should include paragraph content")
        
        # Verify no strings with '.get' error messages in the content
        self.assertNotIn("object has no attribute 'get'", csv_content, 
                        "CSV should not contain error messages about 'get' method")
    
    def test_all_output_formats(self):
        """
        Test that the OutputFormatter handles all output formats correctly.
        
        Verifies that JSON, Markdown, HTML, and CSV outputs are generated with proper content.
        """
        # List of formats to test
        formats = ['json', 'md', 'html', 'csv']
        
        for format_type in formats:
            # Generate output
            output_file = self.formatter.save_formatted_output(
                self.document_data,
                self.test_output_dir,
                format_type
            )
            
            # Verify file exists
            self.assertTrue(output_file.exists(), f"{format_type.upper()} file not created")
            
            # Basic content validation
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # File should not be empty
            self.assertGreater(len(content), 0, f"{format_type.upper()} file should not be empty")
            
            # Format-specific validation
            if format_type == 'json':
                # Should be valid JSON
                parsed = json.loads(content)
                self.assertIn('metadata', parsed, "JSON should contain metadata section")
                
            elif format_type == 'md':
                # Should have markdown headings
                self.assertIn('#', content, "Markdown should contain headings")
                
            elif format_type == 'html':
                # Should have HTML structure
                self.assertIn('<!DOCTYPE html>', content, "HTML should have doctype")
                self.assertIn('<html>', content, "HTML should have root element")
                
            elif format_type == 'csv':
                # Should have CSV header
                self.assertTrue(content.startswith("content_type,"), "CSV should start with header row")
                # Should have multiple lines
                lines = content.split('\n')
                self.assertGreater(len(lines), 5, "CSV should have multiple lines")


if __name__ == '__main__':
    unittest.main() 