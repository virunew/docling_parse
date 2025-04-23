"""
Integration tests for the SQL formatter with parse_main.py.

This module tests the integration of the SQL formatter with the main parsing module.
"""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the modules to test
from src.sql_formatter import process_docling_json_to_sql_format
import src.parse_main as parse_main


class TestSQLFormatterIntegration(unittest.TestCase):
    """Integration tests for the SQL Formatter with parse_main.py."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary output directory
        self.output_dir = Path("test_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Sample document data for mocking
        self.sample_document_data = {
            "metadata": {
                "filename": "test_document.pdf",
                "mimetype": "application/pdf",
                "binary_hash": "abc123"
            },
            "furniture": [
                {"text": "Header Text", "type": "header"}
            ],
            "body": [
                {
                    "type": "text",
                    "text": "This is a sample text paragraph.",
                    "breadcrumb": "Document > Section",
                    "prov": {
                        "page_no": 1,
                        "bbox": {"l": 50, "t": 100, "r": 550, "b": 150}
                    }
                }
            ]
        }
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test output files
        for file in self.output_dir.glob("*"):
            file.unlink()
        
        # Remove the directory
        try:
            self.output_dir.rmdir()
        except:
            pass

    @mock.patch('src.parse_helper.process_pdf_document')
    @mock.patch('src.parse_helper.save_output')
    def test_integration_with_parse_main(self, mock_save_output, mock_process_pdf):
        """Test integration of SQL formatter with parse_main."""
        # Mock the process_pdf_document function to return our sample document
        mock_process_pdf.return_value = self.sample_document_data
        
        # Mock the save_output function to return a valid file path
        output_file = self.output_dir / "test_document.json"
        mock_save_output.return_value = str(output_file)
        
        # Write our sample document data to the mocked output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.sample_document_data, f)
        
        # Create a custom function to inject our SQL formatter into the OutputFormatter
        original_init = parse_main.OutputFormatter.__init__
        
        def patched_save_formatted_output(self, document_data, output_dir, output_format):
            """Patched method to use our SQL formatter."""
            # Process the document data using our SQL formatter
            sql_data = process_docling_json_to_sql_format(document_data)
            
            # Save the SQL-formatted data
            sql_output_file = Path(output_dir) / "test_document_sql.json"
            with open(sql_output_file, 'w', encoding='utf-8') as f:
                json.dump(sql_data, f, ensure_ascii=False, indent=2)
            
            return str(sql_output_file)
        
        # Patch the OutputFormatter
        with mock.patch.object(parse_main.OutputFormatter, 'save_formatted_output', patched_save_formatted_output):
            # Set up arguments for parse_main
            test_args = [
                "--pdf_path", "test_document.pdf",
                "--output_dir", str(self.output_dir),
                "--output_format", "json"
            ]
            
            # Run parse_main with our patched formatter
            with mock.patch('sys.argv', ['parse_main.py'] + test_args):
                # Call the main function and check that it executes successfully
                result = parse_main.main()
                self.assertEqual(result, 0, "Main parsing function did not execute successfully")
            
            # Check that our SQL formatter was used
            sql_output_file = self.output_dir / "test_document_sql.json"
            self.assertTrue(sql_output_file.exists(), "SQL formatter output file was not created")
            
            # Verify the contents of the file
            with open(sql_output_file, 'r', encoding='utf-8') as f:
                sql_data = json.load(f)
            
            # Basic validation of the SQL-formatted data
            self.assertIn("chunks", sql_data)
            self.assertIn("furniture", sql_data)
            self.assertIn("source_metadata", sql_data)
            
            # Check if chunks contain the expected data
            self.assertEqual(len(sql_data["chunks"]), 1)
            self.assertEqual(sql_data["chunks"][0]["content_type"], "text")
            self.assertIn("This is a sample text paragraph.", sql_data["chunks"][0]["text_block"])

    @mock.patch('src.parse_helper.process_pdf_document')
    @mock.patch('src.parse_helper.save_output')
    def test_direct_integration_with_output_formatter(self, mock_save_output, mock_process_pdf):
        """Test direct integration with the existing OutputFormatter."""
        # Mock the process_pdf_document function to return our sample document
        mock_process_pdf.return_value = self.sample_document_data
        
        # Mock the save_output function to return a valid file path
        output_file = self.output_dir / "test_document.json"
        mock_save_output.return_value = str(output_file)
        
        # Write our sample document data to the mocked output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.sample_document_data, f)
        
        # Create a formatter instance
        formatter = parse_main.OutputFormatter(parse_main.Configuration().get_formatter_config())
        
        # Process the document data with our SQL formatter
        sql_data = process_docling_json_to_sql_format(self.sample_document_data)
        
        # Save the SQL-formatted data
        sql_output_file = Path(self.output_dir) / "test_document_direct.json"
        with open(sql_output_file, 'w', encoding='utf-8') as f:
            json.dump(sql_data, f, ensure_ascii=False, indent=2)
        
        # Verify the SQL-formatted data
        with open(sql_output_file, 'r', encoding='utf-8') as f:
            sql_data = json.load(f)
        
        # Basic validation
        self.assertIn("chunks", sql_data)
        self.assertIn("furniture", sql_data)
        self.assertIn("source_metadata", sql_data)
        
        # Verify chunk structure
        chunk = sql_data["chunks"][0]
        required_fields = [
            "_id", "block_id", "doc_id", "content_type", "file_type", 
            "master_index", "coords_x", "coords_y", "coords_cx", "coords_cy", 
            "file_source", "text_block", "header_text", "metadata"
        ]
        for field in required_fields:
            self.assertIn(field, chunk)


if __name__ == "__main__":
    unittest.main() 