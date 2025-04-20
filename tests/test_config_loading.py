#!/usr/bin/env python3
"""
Tests for configuration file loading in parse_main.py
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the docling imports
sys.modules['docling.document'] = MagicMock()
sys.modules['docling.converter'] = MagicMock()
sys.modules['docling.settings'] = MagicMock()
sys.modules['docling.pdf.options'] = MagicMock()

# Import after mocking
from src.parse_main import process_pdf_document

class TestConfigFileLoading(unittest.TestCase):
    """Test cases for configuration file loading functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.pdf_path = "dummy.pdf"
        self.output_dir = "test_output"
        self.config_file = str(Path("docling_config.yaml").absolute())
        
        # Create a mock PDF file
        with open(self.pdf_path, "w") as f:
            f.write("Mock PDF content")
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove the mock PDF file
        if os.path.exists(self.pdf_path):
            os.remove(self.pdf_path)
            
        # Remove the test output directory if it exists
        if os.path.exists(self.output_dir):
            import shutil
            shutil.rmtree(self.output_dir)
    
    @patch("src.parse_main.DocumentConverter")
    @patch("src.parse_main.build_element_map")
    def test_config_file_loading(self, mock_build_element_map, mock_doc_converter):
        """Test that configuration file is properly loaded and used."""
        # Configure mocks
        converter_instance = mock_doc_converter.return_value
        conversion_result = unittest.mock.MagicMock()
        conversion_result.status = "success"
        conversion_result.document = unittest.mock.MagicMock()
        conversion_result.document.pages = []
        converter_instance.convert.return_value = conversion_result
        
        mock_build_element_map.return_value = {}
        
        # Call the function with a config file
        process_pdf_document(self.pdf_path, self.output_dir, self.config_file)
        
        # Check that DocumentConverter was initialized correctly (without config_file parameter)
        # and that allow_external_plugins was set to True for the pipeline options
        args, kwargs = mock_doc_converter.call_args
        
        # Verify format_options
        self.assertIn("format_options", kwargs)
        
        # Verify config_file is not in kwargs
        self.assertNotIn("config_file", kwargs)
        
        # Verify DOCLING_CONFIG_FILE environment variable was set
        self.assertEqual(os.environ.get("DOCLING_CONFIG_FILE"), self.config_file)
        
        # Check that allow_external_plugins was set to True in one of the pipeline options
        format_options = kwargs["format_options"]
        pipeline_options_found = False
        
        for fmt_option in format_options.values():
            if hasattr(fmt_option, "pipeline_options") and fmt_option.pipeline_options:
                pipeline_options_found = True
                self.assertTrue(fmt_option.pipeline_options.allow_external_plugins)
                
        self.assertTrue(pipeline_options_found, "Pipeline options with allow_external_plugins not found")


if __name__ == "__main__":
    unittest.main() 