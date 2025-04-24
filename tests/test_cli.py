"""
Command-line interface tests for parse_main.py.

This module tests the command-line interface of the main parser application,
focusing on the SQL format options.
"""

import os
import json
import unittest
import subprocess
import tempfile
from pathlib import Path
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestCommandLineInterface(unittest.TestCase):
    """Test the command-line interface of parse_main.py."""

    def setUp(self):
        """Set up test fixtures."""
        # Path to test PDF
        self.test_pdf = os.path.join(os.path.dirname(__file__), 'data', 'sample.pdf')
        
        # Create a temporary directory for outputs
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name
        
        # Path to the main script
        self.main_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'parse_main.py')
        
        # Skip if test PDF not found
        if not os.path.exists(self.test_pdf):
            self.skipTest("Test PDF file not found")
    
    def tearDown(self):
        """Clean up after test."""
        self.temp_dir.cleanup()
    
    def test_basic_command_line(self):
        """Test basic command-line usage."""
        # Run the parser with default options
        cmd = [
            sys.executable,
            self.main_script,
            '--pdf_path', self.test_pdf,
            '--output_dir', self.output_dir
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check command ran successfully
        self.assertEqual(0, result.returncode, f"Command failed with: {result.stderr}")
        
        # Check output files exist
        pdf_name = Path(self.test_pdf).stem
        expected_output = os.path.join(self.output_dir, f"{pdf_name}.json")
        self.assertTrue(os.path.exists(expected_output), f"Output file not found: {expected_output}")
    
    def test_sql_format_option(self):
        """Test the SQL format option."""
        # Run the parser with SQL format
        cmd = [
            sys.executable,
            self.main_script,
            '--pdf_path', self.test_pdf,
            '--output_dir', self.output_dir,
            '--output-format', 'sql'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check command ran successfully
        self.assertEqual(0, result.returncode, f"Command failed with: {result.stderr}")
        
        # Check output files exist
        pdf_name = Path(self.test_pdf).stem
        expected_output = os.path.join(self.output_dir, f"{pdf_name}_sql.json")
        self.assertTrue(os.path.exists(expected_output), f"SQL output file not found: {expected_output}")
        
        # Validate the output format
        with open(expected_output, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check the output structure
        self.assertIn("chunks", data)
        self.assertIn("furniture", data)
        self.assertIn("source_metadata", data)
    
    def test_sql_dialect_option(self):
        """Test the SQL dialect option."""
        # Test each supported dialect
        for dialect in ["postgresql", "mysql", "sqlite"]:
            # Run the parser with SQL format and specified dialect
            cmd = [
                sys.executable,
                self.main_script,
                '--pdf_path', self.test_pdf,
                '--output_dir', self.output_dir,
                '--output-format', 'sql',
                '--sql-inserts',
                '--sql-dialect', dialect
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Check command ran successfully
            self.assertEqual(0, result.returncode, f"Command failed with dialect {dialect}: {result.stderr}")
            
            # Check output files exist
            pdf_name = Path(self.test_pdf).stem
            expected_output = os.path.join(self.output_dir, f"{pdf_name}_inserts.sql")
            self.assertTrue(os.path.exists(expected_output), f"SQL inserts file for {dialect} not found")
    
    def test_standardized_format_option(self):
        """Test the standardized format option."""
        # Run the parser with SQL format and standardized format option
        cmd = [
            sys.executable,
            self.main_script,
            '--pdf_path', self.test_pdf,
            '--output_dir', self.output_dir,
            '--output-format', 'sql',
            '--standardized-format'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check command ran successfully
        self.assertEqual(0, result.returncode, f"Command failed with: {result.stderr}")
        
        # Check output files exist
        pdf_name = Path(self.test_pdf).stem
        expected_output = os.path.join(self.output_dir, f"{pdf_name}_standardized.json")
        self.assertTrue(os.path.exists(expected_output), f"Standardized output file not found: {expected_output}")
    
    def test_sql_inserts_option(self):
        """Test the SQL inserts option."""
        # Run the parser with SQL format and inserts option
        cmd = [
            sys.executable,
            self.main_script,
            '--pdf_path', self.test_pdf,
            '--output_dir', self.output_dir,
            '--output-format', 'sql',
            '--sql-inserts'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check command ran successfully
        self.assertEqual(0, result.returncode, f"Command failed with: {result.stderr}")
        
        # Check output files exist
        pdf_name = Path(self.test_pdf).stem
        expected_output = os.path.join(self.output_dir, f"{pdf_name}_inserts.sql")
        self.assertTrue(os.path.exists(expected_output), f"SQL inserts file not found: {expected_output}")
        
        # Validate the SQL content
        with open(expected_output, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Check for expected SQL statements
        self.assertIn("INSERT INTO", sql_content)
        self.assertIn("VALUES", sql_content)


if __name__ == "__main__":
    unittest.main() 