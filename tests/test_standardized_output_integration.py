#!/usr/bin/env python3
"""
Integration tests for standardized output integration with parse_main.py

This module tests that the parse_main.py file correctly integrates with
the standardized output function.
"""

import unittest
from unittest.mock import patch


class TestStandardizedOutputIntegration(unittest.TestCase):
    """Test case for standardized output integration with parse_main.py."""

    def test_standardized_output_import(self):
        """Test that parse_main.py imports the standardized output function."""
        # Import the parse_main module without executing it
        with patch('sys.argv', ['parse_main.py']):
            import parse_main
            
            # Check that save_standardized_output is imported
            self.assertTrue(hasattr(parse_main, 'save_standardized_output'), 
                          "save_standardized_output should be imported in parse_main.py")
    
    def test_main_function_calls_standardized_output(self):
        """Test that the main function calls save_standardized_output for non-SQL formats."""
        with patch('sys.argv', ['parse_main.py']):
            import parse_main
            
            # Read the source code of parse_main.py to check for standardized output integration
            with open('parse_main.py', 'r') as f:
                source_code = f.read()
            
            # Check if standardized output is called in the main function
            self.assertIn('standardized_output_file = save_standardized_output(', source_code,
                        "save_standardized_output should be called in main()")
            
            # Check if the standardized output call is after the formatter
            # This ensures the correct order of operations
            formatter_index = source_code.find('formatter = OutputFormatter(')
            standardized_output_index = source_code.find('standardized_output_file = save_standardized_output(')
            
            self.assertGreater(standardized_output_index, formatter_index,
                            "save_standardized_output should be called after creating the formatter")
    
    @patch('parse_main.process_pdf_document')
    @patch('parse_main.save_output')
    @patch('parse_main.save_standardized_output')
    def test_standardized_output_usage(self, mock_save_standardized, mock_save_output, mock_process_pdf):
        """Test that save_standardized_output is used for non-SQL formats."""
        with patch('sys.argv', ['parse_main.py', '--output_format', 'json', '--pdf_path', 'dummy.pdf']):
            import parse_main
            
            # Setup mocks
            mock_process_pdf.return_value = {'name': 'test_document'}
            mock_save_output.return_value = 'output.json'
            mock_save_standardized.return_value = 'standardized_output.json'
            
            # Patch file opening to return mock document data
            mock_file_content = '{"name": "test_document"}'
            mock_open = unittest.mock.mock_open(read_data=mock_file_content)
            with patch('builtins.open', mock_open):
                # Patch Path.exists to prevent file not found errors
                with patch('pathlib.Path.exists', return_value=True):
                    # Skip validation errors
                    with patch.object(parse_main.Configuration, 'validate', return_value=[]):
                        # Skip formatter to simplify test
                        with patch('parse_main.OutputFormatter'):
                            # Run the main function with mocked setup_logging
                            with patch('parse_main.setup_logging'):
                                parse_main.main()
            
            # Check that save_standardized_output was called
            mock_save_standardized.assert_called_once()


if __name__ == '__main__':
    unittest.main() 