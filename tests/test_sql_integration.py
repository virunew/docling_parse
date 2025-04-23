"""
SQL Formatter Integration Test

This module tests the integration of the SQL formatter with parse_main.py.
It verifies that the main function correctly processes documents and 
generates SQL-formatted output.
"""

import unittest
import os
import json
import tempfile
import shutil
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import docling_fix to handle docling import issues
import docling_fix

class TestSQLIntegration(unittest.TestCase):
    """Integration tests for the SQL formatter with parse_main.py."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for output
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)
        
        # Create a dict-based mock document (not using MagicMock)
        # This structure matches what SQLFormatter expects
        self.mock_document = {
            "pdf_name": "test_document.pdf",
            "pdf_info": {
                "Title": "Test Document",
                "Author": "Test Author",
                "Subject": "Test Subject",
                "Creator": "Test Creator",
                "Producer": "Test Producer",
                "CreationDate": "2023-01-01",
                "ModDate": "2023-01-02"
            },
            "num_pages": 5,
            "elements": [
                {
                    "type": "text",
                    "page_num": 1,
                    "text": "This is the title of the document",
                    "font_size": 16
                },
                {
                    "type": "text",
                    "page_num": 1,
                    "text": "This is the abstract of the document",
                    "font_size": 12
                },
                {
                    "type": "text",
                    "page_num": 2,
                    "text": "This is content on page 2",
                    "font_size": 12
                }
            ]
        }
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)
    
    def test_sql_formatter_direct_integration(self):
        """Test direct integration with SQLFormatter."""
        # Import the SQLFormatter
        from src.sql_formatter import SQLFormatter
        
        # Create formatter instance
        formatter = SQLFormatter()
        
        # Format the document
        formatted_data = formatter.format_as_sql_json(self.mock_document)
        
        # Verify structure
        self.assertIn("source", formatted_data)
        self.assertIn("furniture", formatted_data)
        self.assertIn("chunks", formatted_data)
        
        # Check document metadata
        self.assertEqual(formatted_data["source"]["file_name"], "test_document.pdf")
        self.assertEqual(formatted_data["source"]["title"], "Test Document")
        self.assertEqual(formatted_data["source"]["author"], "Test Author")
        
        # Verify chunks have content
        self.assertTrue(len(formatted_data["chunks"]) > 0)
    
    def test_sql_formatter_output_file(self):
        """Test that the SQLFormatter saves output correctly."""
        # Import the SQLFormatter
        from src.sql_formatter import SQLFormatter
        
        # Create formatter instance
        formatter = SQLFormatter()
        
        # Save the formatted output
        output_file = formatter.save_formatted_output(self.mock_document, str(self.output_dir))
        
        # Verify the file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Verify the file is valid JSON
        with open(output_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # Check structure
        self.assertIn("source", content)
        self.assertIn("furniture", content)
        self.assertIn("chunks", content)
    
    def test_verify_format_document_integration(self):
        """Test that parse_main has the SQLFormatter included for 'sql' format."""
        # Read parse_main.py to check for SQLFormatter import and usage
        parse_main_path = Path(__file__).parent.parent / "parse_main.py"
        with open(parse_main_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for import of SQLFormatter
        self.assertIn("from src.sql_formatter import SQLFormatter", content)
        
        # Check for usage in main() function
        self.assertIn("if config.output_format.lower() == \"sql\":", content)
        self.assertIn("sql_formatter = SQLFormatter()", content)
        
        # This verifies that parse_main.py includes the SQLFormatter


if __name__ == "__main__":
    unittest.main() 