"""
Unit tests for the parse_main module.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import json
import logging

# Add the parent directory to the path so we can import the module
sys.path.append(str(Path(__file__).parent.parent))

from src.parse_main import (
    Configuration,
    parse_arguments,
    setup_logging,
    process_pdf_document,
    save_output,
    main
)


class TestConfiguration(unittest.TestCase):
    """Tests for the Configuration class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Save original environment variables
        self.original_environ = os.environ.copy()
        
        # Create a sample PDF file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf_path = Path(self.temp_dir.name) / "test.pdf"
        self.pdf_path.touch()  # Create an empty file
        
        # Create a sample config file for testing
        self.config_path = Path(self.temp_dir.name) / "config.json"
        self.config_path.write_text("{}")
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_environ)
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = Configuration()
        
        self.assertIsNone(config.pdf_path)
        self.assertEqual(config.output_dir, "output")
        self.assertEqual(config.log_level, "INFO")
        self.assertIsNone(config.config_file)
    
    def test_environment_variables(self):
        """Test that environment variables override default values."""
        # Set environment variables
        os.environ["DOCLING_PDF_PATH"] = str(self.pdf_path)
        os.environ["DOCLING_OUTPUT_DIR"] = "env_output"
        os.environ["DOCLING_LOG_LEVEL"] = "DEBUG"
        os.environ["DOCLING_CONFIG_FILE"] = str(self.config_path)
        
        config = Configuration()
        
        self.assertEqual(config.pdf_path, str(self.pdf_path))
        self.assertEqual(config.output_dir, "env_output")
        self.assertEqual(config.log_level, "DEBUG")
        self.assertEqual(config.config_file, str(self.config_path))
    
    def test_update_from_args(self):
        """Test that command-line arguments override environment variables."""
        # Set environment variables
        os.environ["DOCLING_PDF_PATH"] = "env_test.pdf"
        os.environ["DOCLING_OUTPUT_DIR"] = "env_output"
        
        # Create mock args
        args = MagicMock()
        args.pdf_path = str(self.pdf_path)
        args.output_dir = "arg_output"
        args.log_level = None
        args.config_file = None
        
        config = Configuration()
        config.update_from_args(args)
        
        # Check that args override env vars when provided
        self.assertEqual(config.pdf_path, str(self.pdf_path))
        self.assertEqual(config.output_dir, "arg_output")
        
        # Check that env vars are used when args not provided
        self.assertEqual(config.log_level, "INFO")  # Default, as neither env nor arg provided
    
    def test_validate_valid_config(self):
        """Test that a valid configuration passes validation."""
        config = Configuration()
        config.pdf_path = str(self.pdf_path)
        config.log_level = "DEBUG"
        
        errors = config.validate()
        self.assertEqual(errors, [])
    
    def test_validate_missing_pdf_path(self):
        """Test that validation fails when PDF path is missing."""
        config = Configuration()
        config.pdf_path = None
        
        errors = config.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("PDF file path is required", errors[0])
    
    def test_validate_nonexistent_pdf(self):
        """Test that validation fails when PDF file doesn't exist."""
        config = Configuration()
        config.pdf_path = "nonexistent.pdf"
        
        errors = config.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("PDF file not found", errors[0])
    
    def test_validate_invalid_log_level(self):
        """Test that validation fails with invalid log level."""
        config = Configuration()
        config.pdf_path = str(self.pdf_path)
        config.log_level = "INVALID"
        
        errors = config.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("Invalid log level", errors[0])
    
    def test_validate_nonexistent_config_file(self):
        """Test that validation fails when config file doesn't exist."""
        config = Configuration()
        config.pdf_path = str(self.pdf_path)
        config.config_file = "nonexistent.json"
        
        errors = config.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("Config file not found", errors[0])


class TestParseArguments(unittest.TestCase):
    """Tests for the parse_arguments function."""
    
    @patch('argparse.ArgumentParser.parse_args')
    def test_parse_arguments(self, mock_parse_args):
        """Test that arguments are parsed correctly."""
        # Set up mock return value
        mock_args = MagicMock()
        mock_args.pdf_path = "test.pdf"
        mock_args.output_dir = "output"
        mock_args.log_level = "INFO"
        mock_args.config_file = None
        mock_parse_args.return_value = mock_args
        
        # Call the function
        args = parse_arguments()
        
        # Check the results
        self.assertEqual(args.pdf_path, "test.pdf")
        self.assertEqual(args.output_dir, "output")
        self.assertEqual(args.log_level, "INFO")
        self.assertIsNone(args.config_file)


class TestSetupLogging(unittest.TestCase):
    """Tests for the setup_logging function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Save the original logger level and handlers
        self.original_level = logging.getLogger().level
        self.original_handlers = logging.getLogger().handlers.copy()
        self.original_logger_level = logging.getLogger("docling_parser").level
        self.original_logger_handlers = logging.getLogger("docling_parser").handlers.copy()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore the original logger level and handlers
        logging.getLogger().setLevel(self.original_level)
        
        # Remove any handlers we added
        for handler in logging.getLogger().handlers:
            if handler not in self.original_handlers:
                logging.getLogger().removeHandler(handler)
        
        # Restore the original docling_parser logger
        docling_logger = logging.getLogger("docling_parser")
        docling_logger.setLevel(self.original_logger_level)
        
        for handler in docling_logger.handlers:
            if handler not in self.original_logger_handlers:
                docling_logger.removeHandler(handler)
    
    @patch('pathlib.Path.mkdir')
    @patch('logging.FileHandler')
    def test_setup_logging_debug(self, mock_file_handler, mock_mkdir):
        """Test that logging is set up correctly at DEBUG level."""
        # Set up mocks
        mock_handler = MagicMock()
        mock_file_handler.return_value = mock_handler
        
        # Call the function
        setup_logging("DEBUG")
        
        # Check that the root logger level was set to DEBUG
        self.assertEqual(logging.getLogger().level, logging.DEBUG)
        
        # Check that the docling_parser logger level was set to DEBUG
        self.assertEqual(logging.getLogger("docling_parser").level, logging.DEBUG)
        
        # Check that the file handler was created with the correct level
        mock_file_handler.assert_called_once()
        mock_handler.setLevel.assert_called_once_with(logging.DEBUG)
    
    @patch('pathlib.Path.mkdir')
    @patch('logging.FileHandler')
    def test_setup_logging_info(self, mock_file_handler, mock_mkdir):
        """Test that logging is set up correctly at INFO level."""
        # Set up mocks
        mock_handler = MagicMock()
        mock_file_handler.return_value = mock_handler
        
        # Call the function
        setup_logging("INFO")
        
        # Check that the root logger level was set to INFO
        self.assertEqual(logging.getLogger().level, logging.INFO)
        
        # Check that the docling_parser logger level was set to INFO
        self.assertEqual(logging.getLogger("docling_parser").level, logging.INFO)
        
        # Check that the file handler was created with the correct level
        mock_file_handler.assert_called_once()
        mock_handler.setLevel.assert_called_once_with(logging.INFO)
    
    def test_setup_logging_invalid(self):
        """Test that an invalid log level raises a ValueError."""
        with self.assertRaises(ValueError):
            setup_logging("INVALID")


class MockRect:
    def __init__(self, l=0, t=0, width=100, height=50):
        self.l = l
        self.t = t
        self.width = width
        self.height = height
    
    def to_bounding_box(self):
        return self

class MockCell:
    def __init__(self, text="Sample text", rect=None, from_ocr=False, confidence=None):
        self.text = text
        self.rect = rect or MockRect()
        self.from_ocr = from_ocr
        self.confidence = confidence

class MockPage:
    def __init__(self):
        self.cells = [
            MockCell(text="First paragraph", rect=MockRect(10, 20, 200, 30), from_ocr=True, confidence=0.95),
            MockCell(text="Second paragraph", rect=MockRect(10, 60, 200, 30))
        ]

class MockDocument:
    def __init__(self):
        self.pages = {1: MockPage()}

class MockConversionResult:
    def __init__(self):
        self.document = MockDocument()
        self.images = []

class TestProcessPDFDocument(unittest.TestCase):
    """Tests for the process_pdf_document function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory and PDF file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name) / "output"
        self.pdf_path = Path(self.temp_dir.name) / "test.pdf"
        self.pdf_path.touch()  # Create an empty file
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    @patch('src.parse_main.build_element_map')
    @patch('src.parse_main.DocumentConverter')
    def test_process_pdf_document(self, mock_document_converter, mock_build_element_map):
        """Test that PDFs are processed correctly and element map is built."""
        # Set up mock document converter and conversion result
        mock_converter_instance = MagicMock()
        mock_document_converter.return_value = mock_converter_instance
        
        # Create mock document
        mock_document = MagicMock()
        
        # Create mock pages
        mock_page = MagicMock()
        
        # Create mock segments for the page
        mock_segment = MagicMock()
        mock_segment.text = "Sample text from PDF"
        mock_segment.type.value = "paragraph"
        mock_segment.coordinates.x = 10
        mock_segment.coordinates.y = 10
        mock_segment.coordinates.width = 100
        mock_segment.coordinates.height = 20
        
        # Create mock pictures for the page
        mock_picture = MagicMock()
        mock_picture.caption = "Sample text from PDF"
        mock_picture.coordinates.x = 10
        mock_picture.coordinates.y = 40
        mock_picture.coordinates.width = 200
        mock_picture.coordinates.height = 150
        
        # Mock picture image
        mock_picture.image.pil_image = MagicMock()
        
        # Add mock segments and pictures to the page
        mock_page.segments = [mock_segment]
        mock_page.pictures = [mock_picture]
        
        # Create mock tables
        mock_table = MagicMock()
        mock_table.export_to_markdown.return_value = "| Header |\n|--------|\n| Data   |"
        mock_table.rows = ["header", "data"]
        mock_table.columns = ["col1"]
        
        # Add mock pages and tables to the document
        mock_document.pages = {1: mock_page}
        mock_document.tables = [mock_table]
        
        # Set up mock conversion result
        mock_conv_result = MagicMock()
        mock_conv_result.document = mock_document
        mock_conv_result.input.file.name = "test.pdf"
        mock_conv_result.input.file.stem = "test"
        
        # Set up the converter to return our mock result
        mock_converter_instance.convert.return_value = mock_conv_result
        
        # Set up mock return value for build_element_map
        mock_element_map = {
            "text1": {"text": "Sample text from PDF"},
            "pic1": {"caption": {"$ref": "text1"}}
        }
        mock_build_element_map.return_value = mock_element_map
        
        # Call the function
        result = process_pdf_document(str(self.pdf_path), str(self.output_dir))
        
        # Check that DocumentConverter was called with correct format options
        mock_document_converter.assert_called_once()
        self.assertIn('format_options', mock_document_converter.call_args[1])
        
        # Check that converter.convert was called with the PDF path
        mock_converter_instance.convert.assert_called_once()
        pdf_path_arg = mock_converter_instance.convert.call_args[0][0]
        self.assertEqual(str(pdf_path_arg), str(self.pdf_path))
        
        # Check that build_element_map was called
        mock_build_element_map.assert_called_once()
        
        # The document_data passed to build_element_map should contain texts, pictures, tables and metadata
        doc_data = mock_build_element_map.call_args[0][0]
        self.assertIn('texts', doc_data)
        self.assertIn('pictures', doc_data)
        self.assertIn('tables', doc_data)
        self.assertIn('metadata', doc_data)
        
        # Check that at least one text element was created
        self.assertTrue(len(doc_data['texts']) > 0)
        self.assertEqual(doc_data['texts'][0]['text'], "Sample text from PDF")
        
        # Check the result
        self.assertEqual(result, mock_element_map)
        
        # Verify output directory was created
        self.assertTrue(self.output_dir.exists())
    
    @patch('src.parse_main.DocumentConverter')
    def test_process_pdf_document_error_handling(self, mock_document_converter):
        """Test that PDF processing errors are properly handled."""
        # Set up mock document converter to raise an exception
        mock_converter_instance = MagicMock()
        mock_document_converter.return_value = mock_converter_instance
        mock_converter_instance.convert.side_effect = Exception("PDF processing error")
        
        # Call the function and check that it raises the exception
        with self.assertRaises(Exception) as context:
            process_pdf_document(str(self.pdf_path), str(self.output_dir))
            
        self.assertIn("PDF processing error", str(context.exception))

    @patch('parse_main.convert_pdf')
    def test_process_pdf_document_text_extraction(self, mock_convert):
        # Setup mock
        mock_convert.return_value = MockConversionResult()
        
        # Process document
        result = process_pdf_document(self.pdf_path, self.output_dir)
        
        # Verify text extraction
        self.assertEqual(len(result["texts"]), 2)
        
        # Check first text element
        text1 = result["texts"][0]
        self.assertEqual(text1["text"], "First paragraph")
        self.assertEqual(text1["metadata"]["page"], 1)
        self.assertEqual(text1["metadata"]["position"]["x"], 10)
        self.assertEqual(text1["metadata"]["position"]["y"], 20)
        self.assertEqual(text1["metadata"]["position"]["width"], 200)
        self.assertEqual(text1["metadata"]["position"]["height"], 30)
        self.assertTrue(text1["metadata"]["ocr"])
        self.assertEqual(text1["metadata"]["confidence"], 0.95)
        
        # Check second text element
        text2 = result["texts"][1]
        self.assertEqual(text2["text"], "Second paragraph")
        self.assertEqual(text2["metadata"]["page"], 1)
        self.assertEqual(text2["metadata"]["position"]["x"], 10)
        self.assertEqual(text2["metadata"]["position"]["y"], 60)
        self.assertEqual(text2["metadata"]["position"]["width"], 200)
        self.assertEqual(text2["metadata"]["position"]["height"], 30)
        self.assertFalse(text2["metadata"]["ocr"])
        self.assertIsNone(text2["metadata"]["confidence"])


class TestSaveOutput(unittest.TestCase):
    """Tests for the save_output function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_save_output(self):
        """Test that output is saved correctly."""
        # Create test data
        element_map = {"text1": {"text": "Sample text from PDF"}}
        
        # Call the function
        save_output(element_map, self.output_dir)
        
        # Check that the output file was created
        output_file = self.output_dir / "element_map.json"
        self.assertTrue(output_file.exists())
        
        # Check the contents of the output file
        with open(output_file) as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, element_map)


class TestMainFunction(unittest.TestCase):
    """Tests for the main function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory and PDF file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf_path = Path(self.temp_dir.name) / "test.pdf"
        self.pdf_path.touch()  # Create an empty file
        
        # Save original environment variables
        self.original_environ = os.environ.copy()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_environ)
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    @patch('src.parse_main.parse_arguments')
    @patch('src.parse_main.setup_logging')
    @patch('src.parse_main.process_pdf_document')
    @patch('src.parse_main.save_output')
    def test_main_successful(self, mock_save, mock_process, mock_setup_logging, mock_parse_args):
        """Test that main function runs successfully with valid inputs."""
        # Set up mock return values
        mock_args = MagicMock()
        mock_args.pdf_path = str(self.pdf_path)
        mock_args.output_dir = "output"
        mock_args.log_level = "INFO"
        mock_args.config_file = None
        mock_parse_args.return_value = mock_args
        
        mock_element_map = {"text1": {"text": "Sample text from PDF"}}
        mock_process.return_value = mock_element_map
        
        # Call the function
        exit_code = main()
        
        # Check that the function completed successfully
        self.assertEqual(exit_code, 0)
        
        # Check that the right functions were called
        mock_setup_logging.assert_called_once_with("INFO")
        mock_process.assert_called_once_with(str(self.pdf_path), "output")
        mock_save.assert_called_once_with(mock_element_map, "output")
    
    @patch('src.parse_main.parse_arguments')
    def test_main_validation_error(self, mock_parse_args):
        """Test that main function returns an error when validation fails."""
        # Set up mock return values
        mock_args = MagicMock()
        mock_args.pdf_path = "nonexistent.pdf"
        mock_args.output_dir = "output"
        mock_args.log_level = "INFO"
        mock_args.config_file = None
        mock_parse_args.return_value = mock_args
        
        # Call the function
        exit_code = main()
        
        # Check that the function returned an error
        self.assertEqual(exit_code, 1)
    
    @patch('src.parse_main.parse_arguments')
    @patch('src.parse_main.setup_logging')
    @patch('src.parse_main.process_pdf_document')
    def test_main_processing_error(self, mock_process, mock_setup_logging, mock_parse_args):
        """Test that main function handles exceptions during processing."""
        # Set up mock return values
        mock_args = MagicMock()
        mock_args.pdf_path = str(self.pdf_path)
        mock_args.output_dir = "output"
        mock_args.log_level = "INFO"
        mock_args.config_file = None
        mock_parse_args.return_value = mock_args
        
        # Make process_pdf_document raise an exception
        mock_process.side_effect = Exception("Processing error")
        
        # Call the function
        exit_code = main()
        
        # Check that the function returned an error
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main() 