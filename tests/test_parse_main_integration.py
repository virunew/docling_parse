#!/usr/bin/env python3
"""
Integration Test for Parse Main Flow

This script tests the main parsing flow with image extraction integration.
It verifies that the entire pipeline works correctly from end to end.
"""

import json
import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path
import unittest
from unittest import mock

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the mock docling module
from save_output import save_output
from tests.mock_docling import (
    DocumentConverter, 
    PdfFormatOption, 
    InputFormat, 
    PdfPipelineOptions,
    ConversionResult
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestParseMainIntegration(unittest.TestCase):
    """Test suite for the main parsing flow with image extraction."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for output files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Get a sample PDF path from environment variable or use a default test file
        self.sample_pdf_path = os.environ.get(
            "TEST_PDF_PATH", 
            str(Path(__file__).parent / "data" / "sample.pdf")
        )
        
        # Store original environment variables
        self.original_env = {
            "DOCLING_PDF_PATH": os.environ.get("DOCLING_PDF_PATH"),
            "DOCLING_OUTPUT_DIR": os.environ.get("DOCLING_OUTPUT_DIR"),
            "DOCLING_LOG_LEVEL": os.environ.get("DOCLING_LOG_LEVEL"),
            "DOCLING_CONFIG_FILE": os.environ.get("DOCLING_CONFIG_FILE"),
        }
        
        # Set environment variables for testing
        os.environ["DOCLING_PDF_PATH"] = self.sample_pdf_path
        os.environ["DOCLING_OUTPUT_DIR"] = str(self.output_dir)
        os.environ["DOCLING_LOG_LEVEL"] = "INFO"
        
        # Create patcher for docling module
        self.docling_patcher = mock.patch.dict(sys.modules, {
            'docling.document_converter': mock.MagicMock(),
            'docling.datamodel.base_models': mock.MagicMock(),
            'docling.datamodel.pipeline_options': mock.MagicMock(),
            'docling.datamodel.document': mock.MagicMock()
        })
        
        # Start the patcher
        self.docling_patcher.start()
        
        # After patching the modules, import the modules to test
        from src.parse_main import main, Configuration, process_pdf_document
        self.main = main
        self.Configuration = Configuration
        self.process_pdf_document = process_pdf_document
        self.save_output = save_output
    
    def tearDown(self):
        """Clean up after the test."""
        # Stop the patcher
        self.docling_patcher.stop()
        
        # Restore original environment variables
        for key, value in self.original_env.items():
            if value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = value
        
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_configuration_from_env(self):
        """Test that configuration is correctly loaded from environment variables."""
        # Skip if the test file doesn't exist
        if not Path(self.sample_pdf_path).exists():
            self.skipTest(f"Test PDF file not found: {self.sample_pdf_path}")
        
        # Create a configuration object
        config = self.Configuration()
        
        # Verify that the configuration was loaded from environment variables
        self.assertEqual(config.pdf_path, self.sample_pdf_path)
        self.assertEqual(config.output_dir, str(self.output_dir))
        self.assertEqual(config.log_level, "INFO")
    
    @mock.patch('src.parse_main.DocumentConverter')
    @mock.patch('src.element_map_builder.build_element_map')
    def test_process_pdf_document(self, mock_build_element_map, mock_converter_class):
        """Test the process_pdf_document function with image extraction."""
        # Skip if the test file doesn't exist
        if not Path(self.sample_pdf_path).exists():
            self.skipTest(f"Test PDF file not found: {self.sample_pdf_path}")
        
        # Set up mocks
        mock_converter = mock_converter_class.return_value
        mock_document = mock.MagicMock()
        mock_document.name = "sample"
        mock_document.pages = [mock.MagicMock(), mock.MagicMock()]
        
        mock_converter.convert.return_value = ConversionResult(
            document=mock_document
        )
        
        mock_build_element_map.return_value = {
            "flattened_sequence": [
                {"id": "text1", "text": "Text before image"},
                {"id": "img1", "type": "picture"},
                {"id": "text2", "text": "Text after image"}
            ]
        }
        
        # Process the PDF document
        docling_document = self.process_pdf_document(
            self.sample_pdf_path, 
            self.output_dir
        )
        
        # Verify that the document was processed
        self.assertIsNotNone(docling_document)
        
        # Verify that the mocks were called correctly
        mock_converter_class.assert_called_once()
        mock_converter.convert.assert_called_once()
        
        # Save the output to verify integration
        output_file = self.save_output(docling_document, self.output_dir)
        
        # Verify that the output file exists
        self.assertTrue(output_file.exists())
    
    @mock.patch('sys.argv')
    @mock.patch('src.parse_main.process_pdf_document')
    @mock.patch('src.parse_main.save_output')
    def test_end_to_end_flow(self, mock_save_output, mock_process_pdf_document, mock_argv):
        """Test the end-to-end parsing flow with image extraction."""
        # Skip if the test file doesn't exist
        if not Path(self.sample_pdf_path).exists():
            self.skipTest(f"Test PDF file not found: {self.sample_pdf_path}")
        
        # Set up test argv
        mock_argv.__getitem__.side_effect = [
            "parse_main.py", 
            "--pdf", self.sample_pdf_path,
            "--output", str(self.output_dir),
            "--log-level", "INFO"
        ]
        
        # Set up mock docling document
        mock_document = mock.MagicMock()
        mock_document.name = Path(self.sample_pdf_path).stem
        
        # Set up mock return values
        mock_process_pdf_document.return_value = mock_document
        mock_save_output.return_value = self.output_dir / f"{mock_document.name}.json"
        
        # Run the main function
        result = self.main()
        
        # Verify that the main function completed successfully
        self.assertEqual(result, 0)
        
        # Verify that the mocks were called correctly
        mock_process_pdf_document.assert_called_once()
        mock_save_output.assert_called_once()


def main():
    """Run the tests."""
    unittest.main()


if __name__ == "__main__":
    main() 