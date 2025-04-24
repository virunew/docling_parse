#!/usr/bin/env python3
"""
Integration tests for SQL formatter integration with parse_main.py

This module tests that the parse_main.py file correctly integrates with
the SQL formatter and standardized output functions.
"""

import unittest
from unittest.mock import patch


class TestSQLIntegration(unittest.TestCase):
    """Test case for SQL formatter integration with parse_main.py."""

    def test_sql_formatter_imports(self):
        """Test that parse_main.py imports the SQL formatter."""
        # Import the parse_main module without executing it
        with patch('sys.argv', ['parse_main.py']):
            import parse_main
            
            # Check that SQLFormatter is imported
            self.assertTrue(hasattr(parse_main, 'SQLFormatter'), 
                          "SQLFormatter should be imported in parse_main.py")
            
            # Check that the format_standardized_output is imported
            self.assertTrue(hasattr(parse_main, 'save_standardized_output'), 
                          "save_standardized_output should be imported in parse_main.py")
    
    def test_main_function_sql_handling(self):
        """Test that the main function handles SQL output format."""
        with patch('sys.argv', ['parse_main.py']):
            import parse_main
            
            # Read the source code of parse_main.py to check for SQL integration
            with open('parse_main.py', 'r') as f:
                source_code = f.read()
            
            # Check if the main function handles SQL output format
            self.assertIn('if config.output_format.lower() == "sql":', source_code,
                        "main() should handle SQL output format")
            
            # Check if SQLFormatter is initialized in the main function
            self.assertIn('sql_formatter = SQLFormatter()', source_code,
                        "SQLFormatter should be initialized in main()")
            
            # Check if standardized output is called
            self.assertIn('standardized_output_file = save_standardized_output(', source_code,
                        "save_standardized_output should be called in main()")
    
    @patch('parse_main.process_pdf_document')
    @patch('parse_main.save_output')
    @patch('parse_main.SQLFormatter')
    def test_sql_formatter_usage(self, mock_sql_formatter, mock_save_output, mock_process_pdf):
        """Test that SQLFormatter is used when SQL format is specified."""
        with patch('sys.argv', ['parse_main.py', '--output_format', 'sql', '--pdf_path', 'dummy.pdf']):
            import parse_main
            
            # Setup mocks
            mock_instance = mock_sql_formatter.return_value
            mock_instance.save_formatted_output.return_value = 'output.sql'
            
            # Patch Path.exists to prevent file not found errors
            with patch('pathlib.Path.exists', return_value=True):
                # Skip validation errors
                with patch.object(parse_main.Configuration, 'validate', return_value=[]):
                    # Run the main function
                    with patch('parse_main.setup_logging'):
                        parse_main.main()
            
            # Check that the SQLFormatter was instantiated
            mock_sql_formatter.assert_called_once()
            
            # Check that save_formatted_output was called
            mock_instance.save_formatted_output.assert_called_once()


if __name__ == '__main__':
    unittest.main() 