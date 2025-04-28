#!/usr/bin/env python3
"""
Test for the fix to the DoclingDocument conversion issue in streamlined_processor.py
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the streamlined_process function
from src.streamlined_processor import streamlined_process


class TestDoclingDocumentConversion(unittest.TestCase):
    """Test the DoclingDocument conversion fix in streamlined_processor.py"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock DoclingDocument object
        self.mock_docling_document = Mock()
        self.mock_docling_document.__class__.__name__ = 'DoclingDocument'
        
        # Set up other required parameters
        self.output_dir = "test_output"
        self.pdf_path = "test.pdf"
        self.formatter_config = {
            'include_metadata': True,
            'include_images': True,
            'image_base_url': '',
            'include_page_breaks': True,
            'include_captions': True
        }
        self.output_format = "json"
        
        # Create mocks for expected call chain
        self.mock_dict = {"key": "value"}
        self.mock_fixed_dict = {"key": "fixed_value"}
        self.mock_final_dict = {"key": "final_value"}
        self.mock_output_file = "test_output/output.json"
    
    @patch('src.streamlined_processor.save_output_to_dict')
    @patch('src.streamlined_processor.fix_metadata')
    @patch('src.streamlined_processor.replace_base64_with_file_references')
    @patch('src.streamlined_processor.OutputFormatter')
    def test_docling_document_conversion(self, mock_formatter_class, mock_replace, mock_fix, mock_save_to_dict):
        """Test that a DoclingDocument object is properly converted to a dictionary"""
        # Set up mocks
        mock_save_to_dict.return_value = self.mock_dict
        mock_fix.return_value = self.mock_fixed_dict
        mock_replace.return_value = self.mock_final_dict
        
        # Set up formatter mock
        mock_formatter = MagicMock()
        mock_formatter.save_formatted_output.return_value = self.mock_output_file
        mock_formatter_class.return_value = mock_formatter
        
        # Call the function
        result = streamlined_process(
            self.mock_docling_document,
            self.output_dir,
            self.pdf_path,
            self.formatter_config,
            self.output_format
        )
        
        # Verify the results
        mock_save_to_dict.assert_called_once_with(self.mock_docling_document)
        mock_fix.assert_called_once_with(self.mock_dict, self.output_dir)
        mock_replace.assert_called_once()
        mock_formatter.save_formatted_output.assert_called_once_with(
            self.mock_final_dict,
            self.output_dir,
            self.output_format
        )
        self.assertEqual(result, self.mock_output_file)
    
    @patch('src.streamlined_processor.fix_metadata')
    @patch('src.streamlined_processor.replace_base64_with_file_references')
    @patch('src.streamlined_processor.OutputFormatter')
    def test_dictionary_input(self, mock_formatter_class, mock_replace, mock_fix):
        """Test that a dictionary input is processed correctly without conversion"""
        # Set up dictionary input
        dict_input = {"name": "test_document"}
        
        # Set up mocks
        mock_fix.return_value = self.mock_fixed_dict
        mock_replace.return_value = self.mock_final_dict
        
        # Set up formatter mock
        mock_formatter = MagicMock()
        mock_formatter.save_formatted_output.return_value = self.mock_output_file
        mock_formatter_class.return_value = mock_formatter
        
        # Call the function
        result = streamlined_process(
            dict_input,
            self.output_dir,
            self.pdf_path,
            self.formatter_config,
            self.output_format
        )
        
        # Verify the results
        mock_fix.assert_called_once_with(dict_input, self.output_dir)
        mock_replace.assert_called_once()
        mock_formatter.save_formatted_output.assert_called_once_with(
            self.mock_final_dict,
            self.output_dir,
            self.output_format
        )
        self.assertEqual(result, self.mock_output_file)


if __name__ == '__main__':
    unittest.main() 