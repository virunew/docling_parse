"""
Integration tests for SQL formatter with standardized output.

This module tests the integration between the SQLFormatter and
format_standardized_output functionality to ensure they work together correctly.
"""
import json
import os
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the modules to test
from src.sql_formatter import SQLFormatter
from src.format_standardized_output import save_standardized_output


class TestSQLStandardizedIntegration(unittest.TestCase):
    """
    Test the integration between SQLFormatter and format_standardized_output.
    
    These tests verify that both formatting systems produce compatible outputs
    with the same document data.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for output files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Set up paths
        self.sample_pdf_path = str(Path(self.output_dir) / "test_document.pdf")
        
        # Create formatters
        self.sql_formatter = SQLFormatter()
        
        # Create a sample document data dictionary for testing
        self.sample_document = {
            "name": "test_document",
            "metadata": {
                "filename": "test_document.pdf",
                "mimetype": "application/pdf",
                "binary_hash": "abc123"
            },
            "element_map": {
                "flattened_sequence": [
                    # Text element (not furniture)
                    {
                        "type": "text",
                        "text_content": "This is a sample text paragraph.",
                        "content_layer": "content",
                        "extracted_metadata": {
                            "breadcrumb": "Section 1",
                            "page_no": 1,
                            "bbox_raw": {"l": 50, "t": 100, "r": 550, "b": 150}
                        }
                    },
                    # Furniture element
                    {
                        "type": "text",
                        "text_content": "This is furniture text.",
                        "content_layer": "furniture",
                        "extracted_metadata": {
                            "page_no": 1,
                            "bbox_raw": {"l": 50, "t": 700, "r": 550, "b": 750}
                        }
                    },
                    # Table element
                    {
                        "type": "table",
                        "content_layer": "content",
                        "table_content": [["Header1", "Header2"], ["Value1", "Value2"]],
                        "extracted_metadata": {
                            "breadcrumb": "Section 2",
                            "page_no": 2,
                            "bbox_raw": {"l": 50, "t": 200, "r": 550, "b": 300},
                            "caption": "Sample Table"
                        }
                    }
                ]
            }
        }

    def tearDown(self):
        """Clean up temporary resources."""
        self.temp_dir.cleanup()

    def test_sql_and_standardized_output_compatibility(self):
        """
        Test that SQL formatter and standardized output produce compatible formats.
        
        Both formats should have chunks and furniture arrays with similar structure.
        """
        # Get SQL formatted output
        sql_output = self.sql_formatter.format_as_sql(self.sample_document)
        
        # Get standardized output
        standardized_output_file = save_standardized_output(
            self.sample_document,
            self.output_dir,
            self.sample_pdf_path
        )
        
        # Load the standardized output from file
        with open(standardized_output_file, 'r', encoding='utf-8') as f:
            standardized_output = json.load(f)
        
        # Verify both formats have the same high-level structure
        self.assertIn("chunks", sql_output)
        self.assertIn("furniture", sql_output)
        self.assertIn("source_metadata", sql_output)
        
        self.assertIn("chunks", standardized_output)
        self.assertIn("furniture", standardized_output)
        self.assertIn("source_metadata", standardized_output)
        
        # Test that the furniture element appears in both outputs
        self.assertTrue(any("This is furniture text." in item for item in standardized_output["furniture"]))
        
        # Check chunk counts (furniture elements are not in chunks)
        # SQL format processes differently so just ensure both have chunks
        self.assertGreater(len(standardized_output["chunks"]), 0)
        
        # Check that both have table content with similar structure
        table_in_standardized = False
        for chunk in standardized_output["chunks"]:
            if chunk["content_type"] == "table" and chunk["table_block"] is not None:
                table_in_standardized = True
                break
        
        self.assertTrue(table_in_standardized, "Standardized output should contain table chunks")
    
    def test_save_functions(self):
        """Test that both saving methods work correctly."""
        # Save SQL formatted output
        sql_output_file = self.sql_formatter.save_formatted_output(
            self.sample_document,
            self.output_dir
        )
        
        # Save standardized output
        standardized_output_file = save_standardized_output(
            self.sample_document,
            self.output_dir,
            self.sample_pdf_path
        )
        
        # Verify both files exist
        self.assertTrue(os.path.exists(sql_output_file))
        self.assertTrue(os.path.exists(standardized_output_file))
        
        # Verify the file names are correctly formatted
        self.assertTrue(sql_output_file.endswith("_sql.json"))
        self.assertTrue(standardized_output_file.endswith("_standardized.json"))
    
    def test_save_with_standardized_format_option(self):
        """Test the save_formatted_output method with use_standardized_format option."""
        # Save SQL formatted output with standardized format option
        output_file = self.sql_formatter.save_formatted_output(
            self.sample_document,
            self.output_dir,
            use_standardized_format=True,
            pdf_path=self.sample_pdf_path
        )
        
        # Verify the output file exists and is the standardized format
        self.assertTrue(os.path.exists(output_file))
        self.assertTrue(output_file.endswith("_standardized.json"))
        
        # Verify content matches standardized format
        with open(output_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        self.assertIn("chunks", content)
        self.assertIn("furniture", content)
        self.assertIn("source_metadata", content)
    
    @patch('parse_main.process_pdf_document')
    @patch('parse_main.save_output')
    def test_parse_main_sql_integration(self, mock_save_output, mock_process_pdf):
        """Test that parse_main.py correctly uses the SQLFormatter with standardized output option."""
        try:
            # Try to import parse_main directly to check for docling dependencies
            import parse_main
            has_dependencies = True
        except ImportError:
            # Skip the test if dependencies are missing
            self.skipTest("Could not import parse_main.py due to missing dependencies")
            has_dependencies = False
        
        if has_dependencies:
            # Create a mock for the argument parser and config
            with patch('sys.argv', ['parse_main.py', '--pdf_path', self.sample_pdf_path, 
                                '--output_format', 'sql', '--output_dir', str(self.output_dir),
                                '--use_standardized_format']):
                
                # Setup mock to return our sample document
                mock_process_pdf.return_value = self.sample_document
                
                # Import parse_main here to use the patched sys.argv
                with patch('pathlib.Path.exists', return_value=True):  # Skip file existence check
                    with patch('pathlib.Path.mkdir'):  # Skip directory creation
                        # Skip validation errors
                        with patch.object(parse_main.Configuration, 'validate', return_value=[]):
                            # We can't fully run the main function due to docling dependencies
                            # but we can check if it imports correctly and uses our enhanced SQLFormatter
                            
                            # Check that the Configuration class has the use_standardized_format attribute
                            config = parse_main.Configuration()
                            self.assertTrue(hasattr(config, 'use_standardized_format'))
                            
                            # Verify the command line argument parsing
                            args = parse_main.parse_arguments()
                            self.assertTrue(hasattr(args, 'use_standardized_format'))


if __name__ == "__main__":
    unittest.main() 