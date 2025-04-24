"""
Integration test for SQL formatting functionality.

This module tests the integration of SQL formatting functionality with the main parser 
application, ensuring that the SQL output format works correctly when specified via
command-line arguments or environment variables.
"""

import os
import json
import unittest
import tempfile
import subprocess
from pathlib import Path
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modules to test
from src.sql_formatter import SQLFormatter
from src.sql_insert_generator import SQLInsertGenerator


class TestSQLIntegration(unittest.TestCase):
    """Test the integration of SQL formatting functionality with the main application."""

    def setUp(self):
        """Set up test fixtures."""
        # Path to test PDF
        self.test_pdf = os.path.join(os.path.dirname(__file__), 'data', 'sample.pdf')
        
        # Create a temporary directory for outputs
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name
        
        # Ensure the test PDF exists
        if not os.path.exists(self.test_pdf):
            self.skipTest("Test PDF file not found")
    
    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def test_command_line_sql_format(self):
        """Test the SQL format output when specified via command line."""
        # Skip if running on CI or without actual PDF
        if not os.path.exists(self.test_pdf):
            self.skipTest("Test PDF file not found")
        
        # Run the parser with SQL output format
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'parse_main.py'),
            '--input', self.test_pdf,
            '--output-dir', self.output_dir,
            '--output-format', 'sql'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check command ran successfully
        self.assertEqual(0, result.returncode, f"Command failed with: {result.stderr}")
        
        # Check output files exist
        pdf_name = Path(self.test_pdf).stem
        expected_output = os.path.join(self.output_dir, f"{pdf_name}_sql.json")
        self.assertTrue(os.path.exists(expected_output), f"SQL output file not found: {expected_output}")
        
        # Validate the SQL output format
        with open(expected_output, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check the output structure
        self.assertIn("chunks", data)
        self.assertIn("furniture", data)
        self.assertIn("source_metadata", data)
    
    def test_command_line_sql_insert_statements(self):
        """Test generating SQL INSERT statements when specified via command line."""
        # Skip if running on CI or without actual PDF
        if not os.path.exists(self.test_pdf):
            self.skipTest("Test PDF file not found")
        
        # Run the parser with SQL output format and inserts flag
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'parse_main.py'),
            '--input', self.test_pdf,
            '--output-dir', self.output_dir,
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
        
        # Validate the SQL INSERT statements
        with open(expected_output, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Check for expected SQL statements
        self.assertIn("INSERT INTO", sql_content)
        self.assertIn("documents", sql_content.lower())
        self.assertIn("document_chunks", sql_content.lower())
    
    def test_command_line_sql_dialect_option(self):
        """Test specifying SQL dialect via command line."""
        # Skip if running on CI or without actual PDF
        if not os.path.exists(self.test_pdf):
            self.skipTest("Test PDF file not found")
        
        # Test each supported dialect
        for dialect in ["postgresql", "mysql", "sqlite"]:
            # Run the parser with SQL output format and specified dialect
            cmd = [
                sys.executable,
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'parse_main.py'),
                '--input', self.test_pdf,
                '--output-dir', self.output_dir,
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
            
            # Validate the SQL dialect-specific syntax
            with open(expected_output, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Check for dialect-specific identifiers
            if dialect == "postgresql" or dialect == "sqlite":
                self.assertIn('"documents"', sql_content)
            elif dialect == "mysql":
                self.assertIn('`documents`', sql_content)
    
    def test_standardized_format_option(self):
        """Test the standardized format option for SQL output."""
        # Skip if running on CI or without actual PDF
        if not os.path.exists(self.test_pdf):
            self.skipTest("Test PDF file not found")
        
        # Run the parser with SQL output format and standardized format option
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'parse_main.py'),
            '--input', self.test_pdf,
            '--output-dir', self.output_dir,
            '--output-format', 'sql',
            '--standardized-format'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check command ran successfully
        self.assertEqual(0, result.returncode, f"Command failed with: {result.stderr}")
        
        # Check output files exist - using standardized naming format
        pdf_name = Path(self.test_pdf).stem
        expected_output = os.path.join(self.output_dir, f"{pdf_name}_standardized.json")
        self.assertTrue(os.path.exists(expected_output), f"Standardized output file not found: {expected_output}")
        
        # Validate the standardized output format
        with open(expected_output, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check the standardized output structure
        self.assertIn("chunks", data)
        self.assertIn("furniture", data)
        self.assertIn("source_metadata", data)
        
        # Check that chunks have the expected format
        if data["chunks"]:
            chunk = data["chunks"][0]
            required_fields = [
                "block_id", "content_type", "file_type", "master_index",
                "coords_x", "coords_y", "coords_cx", "coords_cy", 
                "text_block", "header_text", "table_block"
            ]
            for field in required_fields:
                self.assertIn(field, chunk)


if __name__ == "__main__":
    unittest.main() 