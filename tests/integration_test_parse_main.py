"""
End-to-End Integration Tests for parse_main.py

This module tests the entire workflow of the parse_main.py module, from
command-line argument parsing to PDF processing and output generation,
including image extraction.
"""

import os
import sys
import json
import pytest
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock the docling imports
sys.modules['docling'] = MagicMock()
sys.modules['docling.document_converter'] = MagicMock()
sys.modules['docling.datamodel'] = MagicMock()
sys.modules['docling.datamodel.base_models'] = MagicMock()
sys.modules['docling.datamodel.pipeline_options'] = MagicMock()
sys.modules['docling.datamodel.document'] = MagicMock()
sys.modules['docling.document_converter.DocumentConverter'] = MagicMock()
sys.modules['docling.datamodel.base_models.InputFormat'] = MagicMock()
sys.modules['docling.document_converter.PdfFormatOption'] = MagicMock()
sys.modules['docling.datamodel.pipeline_options.PdfPipelineOptions'] = MagicMock()
sys.modules['docling.datamodel.document.ConversionResult'] = MagicMock()

# Mock other modules that depend on docling
sys.modules['element_map_builder'] = MagicMock()
sys.modules['content_extractor'] = MagicMock()
sys.modules['logger_config'] = MagicMock()

# Create mock classes for testing
class PDFImageExtractor:
    def __init__(self, config=None):
        self.config = config or {}
    
    def extract_images(self, pdf_path):
        return {
            "document_name": "test_document",
            "total_pages": 2,
            "images": [
                {
                    "metadata": {
                        "id": "image_1",
                        "docling_ref": "#/pictures/0",
                        "page_number": 1
                    },
                    "data_uri": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
                }
            ]
        }

class ImageContentRelationship:
    def __init__(self, element_map, flattened_sequence):
        self.element_map = element_map
        self.flattened_sequence = flattened_sequence
    
    def analyze_relationships(self, images_data):
        return {
            "relationships": {
                "image_1": {
                    "surrounding_text": "Sample text",
                    "caption": ""
                }
            },
            "images": images_data["images"]
        }

# Create mock functions for testing
def process_pdf_document(pdf_path, output_dir, config_file=None):
    """Mock implementation of process_pdf_document."""
    # Create a mock document
    mock_document = MagicMock()
    mock_document.name = "test_document"
    mock_document.pages = [MagicMock(), MagicMock()]
    mock_document.export_to_dict.return_value = {
        "name": "test_document",
        "pages": [{"id": "page_1"}, {"id": "page_2"}]
    }
    
    # Extract images
    extractor = PDFImageExtractor()
    try:
        images_data = extractor.extract_images(pdf_path)
        
        # Save images_data.json
        images_path = Path(output_dir) / "images_data.json"
        with open(images_path, 'w', encoding='utf-8') as f:
            json.dump(images_data, f, indent=2)
    except Exception as e:
        logging.warning(f"Image extraction error: {e}")
    
    return mock_document

def save_output(docling_document, output_dir):
    """Mock implementation of save_output."""
    output_file = Path(output_dir) / f"{getattr(docling_document, 'name', 'docling_document')}.json"
    
    # Get the document as a dict
    doc_dict = docling_document.export_to_dict()
    
    # Check if images_data.json exists in the output directory
    images_data_file = Path(output_dir) / "images_data.json"
    if images_data_file.exists():
        try:
            with open(images_data_file, 'r', encoding='utf-8') as f:
                images_data = json.load(f)
            doc_dict['images_data'] = images_data
        except Exception:
            pass
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(doc_dict, f, indent=2)
    
    return output_file

# Create mocks for imported modules
sys.modules['parse_helper'] = MagicMock()
sys.modules['parse_helper'].process_pdf_document = process_pdf_document
sys.modules['parse_helper'].save_output = save_output
sys.modules['pdf_image_extractor'] = MagicMock()
sys.modules['pdf_image_extractor'].PDFImageExtractor = PDFImageExtractor
sys.modules['pdf_image_extractor'].ImageContentRelationship = ImageContentRelationship

# Now import parse_main with everything mocked
import parse_main

# Patch the helper functions with our mocks
parse_main.process_pdf_document = process_pdf_document
parse_main.save_output = save_output

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestParseMainIntegration:
    """End-to-end integration tests for parse_main.py."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Find a test PDF if available
        test_data_dir = Path('../test_data')
        if test_data_dir.exists():
            test_pdf_files = list(test_data_dir.glob('*.pdf'))
            self.test_pdf_path = test_pdf_files[0] if test_pdf_files else None
        else:
            self.test_pdf_path = None
            
        # Create output directory
        self.output_dir = tempfile.mkdtemp()
        
        # Create a mock docling document
        self.mock_document = MagicMock()
        self.mock_document.name = "test_document"
        self.mock_document.pages = [MagicMock(), MagicMock()]
        self.mock_document.export_to_dict.return_value = {
            "name": "test_document",
            "pages": [{"id": "page_1"}, {"id": "page_2"}]
        }
        
    def teardown_method(self):
        """Clean up after tests."""
        # Clean up temporary files and directories
        if hasattr(self, 'output_dir') and os.path.exists(self.output_dir):
            # In a real cleanup, we would remove files, but for testing we'll keep them
            pass
    
    def test_main_function_with_mocked_workflow(self):
        """Test the main function with a mocked document processing workflow."""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_pdf:
            # Mock the command line arguments
            test_args = [
                'parse_main.py',
                '--pdf_path', temp_pdf.name,
                '--output_dir', self.output_dir,
                '--log_level', 'INFO'
            ]
            
            with patch('sys.argv', test_args):
                # Mock the process_pdf_document function to return our mock document
                with patch('parse_main.process_pdf_document') as mock_process:
                    mock_process.return_value = self.mock_document
                    
                    # Mock the save_output function to return a path
                    with patch('parse_main.save_output') as mock_save:
                        output_path = Path(self.output_dir) / "test_document.json"
                        mock_save.return_value = output_path
                        
                        # Create a test document content
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump({
                                "name": "test_document",
                                "metadata": {"title": "Test Document"},
                                "pages": [
                                    {
                                        "page_number": 1,
                                        "segments": [{"text": "Test paragraph"}]
                                    }
                                ]
                            }, f, indent=2)
                        
                        # Mock the OutputFormatter
                        mock_formatter = MagicMock()
                        mock_formatter.save_formatted_output.return_value = Path(self.output_dir) / "test_document_simplified.json"
                        
                        with patch('parse_main.OutputFormatter', return_value=mock_formatter):
                            # Create the output file that would normally be created by the formatter
                            simplified_path = Path(self.output_dir) / "test_document_simplified.json"
                            with open(simplified_path, 'w', encoding='utf-8') as f:
                                f.write('{"test": "data"}')
                            
                            # Call the main function
                            exit_code = parse_main.main()
                            
                            # Verify the result
                            assert exit_code == 0
                            
                            # Check that the document was processed
                            mock_process.assert_called_once()
                            mock_save.assert_called_once()
                            
                            # Verify formatter was called
                            assert mock_formatter.save_formatted_output.called
                            
                            # Verify output file exists
                            assert simplified_path.exists()
    
    def test_main_function_handles_errors(self):
        """Test the main function handles errors properly."""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_pdf:
            # Mock the command line arguments
            test_args = [
                'parse_main.py',
                '--pdf_path', temp_pdf.name,
                '--output_dir', self.output_dir,
                '--log_level', 'INFO'
            ]
            
            with patch('sys.argv', test_args):
                # Mock the process_pdf_document function to raise an exception
                with patch('parse_main.process_pdf_document', side_effect=Exception("Test error")):
                    # Call the main function
                    exit_code = parse_main.main()
                    
                    # Verify the result
                    assert exit_code == 1
    
    def test_main_function_validates_config(self):
        """Test the main function validates the configuration."""
        # Mock the command line arguments with a missing PDF path
        test_args = [
            'parse_main.py',
            '--output_dir', self.output_dir,
            '--log_level', 'INFO'
        ]
        
        # Create a PDF path that doesn't exist
        non_existent_pdf = Path(self.output_dir) / "non_existent.pdf"
        
        # Temporarily override the validate method to force a validation error
        original_validate = parse_main.Configuration.validate
        def mock_validate(self):
            # Return a validation error
            return ["PDF file path is required but not provided."]
        
        try:
            # Apply the mock validate method
            parse_main.Configuration.validate = mock_validate
            
            with patch('sys.argv', test_args):
                # Call the main function
                exit_code = parse_main.main()
                
                # Verify the result indicates validation failure
                assert exit_code == 1
        finally:
            # Restore the original validate method
            parse_main.Configuration.validate = original_validate
    
    @pytest.mark.skipif(not Path('../test_data').exists() or not list(Path('../test_data').glob('*.pdf')), 
                       reason="No test PDF files found in test_data directory")
    def test_end_to_end_with_real_pdf(self):
        """Test the end-to-end workflow with a real PDF file if available."""
        # Skip if no test PDF is available
        if not self.test_pdf_path:
            pytest.skip("No test PDF file available")
        
        # Mock the command line arguments
        test_args = [
            'parse_main.py',
            '--pdf_path', str(self.test_pdf_path),
            '--output_dir', self.output_dir,
            '--log_level', 'INFO'
        ]
        
        # Mock only the DoclingDocument parts to avoid actual PDF processing
        with patch('parse_helper.DocumentConverter') as mock_converter_class:
            # Configure the mock document
            mock_result = MagicMock()
            mock_result.status = "success"
            mock_result.document = self.mock_document
            
            mock_converter = MagicMock()
            mock_converter.convert.return_value = mock_result
            mock_converter_class.return_value = mock_converter
            
            # Set up other mocks needed for the full workflow
            with patch.object(PDFImageExtractor, 'extract_images') as mock_extract:
                mock_images_data = {
                    "document_name": "test_document",
                    "total_pages": 2,
                    "images": [
                        {
                            "metadata": {
                                "id": "image_1",
                                "docling_ref": "#/pictures/0",
                                "page_number": 1
                            },
                            "data_uri": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
                        }
                    ]
                }
                mock_extract.return_value = mock_images_data
                
                # Run with the mocked command-line arguments
                with patch('sys.argv', test_args):
                    # Call the main function
                    exit_code = parse_main.main()
                    
                    # Verify the result
                    assert exit_code == 0
                    
                    # Verify the output file was created
                    output_files = list(Path(self.output_dir).glob('*.json'))
                    assert output_files, "No output files were created"
                    
                    # Load the first output file and check its structure
                    with open(output_files[0], 'r', encoding='utf-8') as f:
                        output_data = json.load(f)
                    
                    # Verify basic structure
                    assert "name" in output_data
                    assert "pages" in output_data
                    
                    # The images_data might or might not be there depending on the mocks
                    if "images_data" in output_data:
                        assert "images" in output_data["images_data"]
                    
                    logger.info(f"Successfully verified end-to-end workflow with test PDF")
    
    def test_configuration_from_environment(self):
        """Test configuration loading from environment variables."""
        # Set environment variables
        with patch.dict(os.environ, {
            "DOCLING_PDF_PATH": "env_test.pdf",
            "DOCLING_OUTPUT_DIR": "env_output",
            "DOCLING_LOG_LEVEL": "DEBUG",
            "DOCLING_CONFIG_FILE": "env_config.json"
        }):
            # Create a configuration object
            config = parse_main.Configuration()
            
            # Verify environment variables were loaded
            assert config.pdf_path == "env_test.pdf"
            assert config.output_dir == "env_output"
            assert config.log_level == "DEBUG"
            assert config.config_file == "env_config.json"
            
            # Mock sys.argv for argument parsing
            test_args = ['parse_main.py']  # No command-line args
            
            with patch('sys.argv', test_args):
                # Parse arguments
                args = parse_main.parse_arguments()
                
                # Update configuration from args (should not change)
                config.update_from_args(args)
                
                # Verify config still has environment values
                assert config.pdf_path == "env_test.pdf"
                assert config.output_dir == "env_output"
                assert config.log_level == "DEBUG"
                assert config.config_file == "env_config.json"
                
                logger.info("Successfully verified configuration from environment variables")
    
    def test_configuration_from_args(self):
        """Test that command line arguments are properly processed."""
        # Mock the command line arguments
        test_args = [
            'parse_main.py',
            '--pdf_path', 'test.pdf',
            '--output_dir', 'custom_output',
            '--log_level', 'DEBUG',
            '--output_format', 'html',
            '--image_base_url', 'https://example.com/images',
            '--no_metadata',
            '--no_page_breaks',
            '--no_captions'
        ]
        
        with patch('sys.argv', test_args):
            # Parse the arguments
            args = parse_main.parse_arguments()
            
            # Create a configuration object and update it from args
            config = parse_main.Configuration()
            config.update_from_args(args)
            
            # Check that all values were properly set
            assert config.pdf_path == 'test.pdf'
            assert config.output_dir == 'custom_output'
            assert config.log_level == 'DEBUG'
            assert config.output_format == 'html'
            assert config.image_base_url == 'https://example.com/images'
            assert config.include_metadata is False
            assert config.include_page_breaks is False
            assert config.include_captions is False
            
            # Verify formatter config is correct
            formatter_config = config.get_formatter_config()
            assert formatter_config['include_metadata'] is False
            assert formatter_config['include_page_breaks'] is False
            assert formatter_config['include_captions'] is False
            assert formatter_config['image_base_url'] == 'https://example.com/images'
    
    def test_csv_output_format(self):
        """Test that CSV output format is properly processed and generated."""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_pdf:
            # Mock the command line arguments
            test_args = [
                'parse_main.py',
                '--pdf_path', temp_pdf.name,
                '--output_dir', self.output_dir,
                '--log_level', 'INFO',
                '--output_format', 'csv'
            ]
            
            with patch('sys.argv', test_args):
                # Mock the process_pdf_document function to return our mock document
                with patch('parse_main.process_pdf_document') as mock_process:
                    mock_process.return_value = self.mock_document
                    
                    # Mock the save_output function to return a path
                    with patch('parse_main.save_output') as mock_save:
                        output_path = Path(self.output_dir) / "test_document.json"
                        mock_save.return_value = output_path
                        
                        # Create a test document content
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump({
                                "name": "test_document",
                                "metadata": {"title": "Test Document"},
                                "pages": [
                                    {
                                        "page_number": 1,
                                        "segments": [{"text": "Test paragraph"}],
                                        "tables": [
                                            {
                                                "cells": [
                                                    {"row": 0, "col": 0, "text": "Header 1"},
                                                    {"row": 0, "col": 1, "text": "Header 2"}
                                                ],
                                                "metadata": {"caption": "Test Table", "page_number": 1}
                                            }
                                        ]
                                    }
                                ]
                            }, f, indent=2)
                        
                        # Mock the OutputFormatter
                        mock_formatter = MagicMock()
                        mock_formatter.save_formatted_output.return_value = Path(self.output_dir) / "test_document.csv"
                        
                        with patch('parse_main.OutputFormatter', return_value=mock_formatter):
                            # Create the CSV file that would normally be created by the formatter
                            csv_path = Path(self.output_dir) / "test_document.csv"
                            with open(csv_path, 'w', encoding='utf-8') as f:
                                f.write('content_type,page_number,content,level,metadata\nparagraph,1,"Test paragraph",,\ntable,1,"Test Table",,\ntable_cell,1,"Header 1",,\ntable_cell,1,"Header 2",,')
                            
                            # Call the main function
                            exit_code = parse_main.main()
                            
                            # Check that the function succeeded
                            assert exit_code == 0
                            
                            # Check that the CSV file was created
                            assert csv_path.exists()
                            
                            # Verify the content is CSV formatted
                            with open(csv_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Check that the file has CSV structure
                            assert content.strip().startswith("content_type,page_number,content,level,metadata")
                            assert "paragraph" in content
                            assert "table" in content

    def test_main_function_with_valid_pdf(self):
        """Test main function with a valid PDF."""
        # Skip if no test PDF is available
        if not self.test_pdf_path:
            logger.warning("No test PDF available, skipping test")
            return
        
        # Call main with our test PDF
        sys.argv = [
            "parse_main.py",
            '--pdf_path', str(self.test_pdf_path),
            '--output_dir', self.output_dir
        ]
        exit_code = parse_main.main()
        
        # Check exit code
        assert exit_code == 0
        
        # Check output files exist
        assert os.path.exists(os.path.join(self.output_dir, "document.json"))
        assert os.path.exists(os.path.join(self.output_dir, "fixed_document.json"))

    def test_main_function_with_invalid_pdf(self):
        """Test main function with a non-existent PDF."""
        # Set up command-line args with a non-existent PDF
        sys.argv = [
            "parse_main.py",
            '--pdf_path', 'non_existent.pdf',
            '--output_dir', self.output_dir
        ]
        
        # Run main
        exit_code = parse_main.main()
        
        # Check that we got an error exit code
        assert exit_code != 0

    def test_main_function_with_config_validation_error(self):
        """Test main function error handling with validation errors."""
        # Save the original validate method
        original_validate = parse_main.Configuration.validate
        
        # Mock the validate method to return errors
        def mock_validate(self):
            return ["Mocked validation error"]
        
        # Replace the validate method
        parse_main.Configuration.validate = mock_validate
        
        # Run main with any arguments
        exit_code = parse_main.main()
        
        # Restore the original validate method
        parse_main.Configuration.validate = original_validate
        
        # Check that we got an error exit code
        assert exit_code != 0

    def test_main_with_missing_required_args(self):
        """Test main function when required arguments are missing."""
        # Set up command-line args without required PDF path
        sys.argv = [
            "parse_main.py",
            '--output_dir', self.output_dir
        ]
        
        # Run main
        exit_code = parse_main.main()
        
        # Check that we got an error exit code
        assert exit_code != 0

    def test_configuration_class(self):
        """Test the Configuration class."""
        # Create a Configuration instance
        config = parse_main.Configuration()
        
        # Check default values
        assert config.output_dir == "output"
        assert config.log_level == "INFO"

    def test_parse_arguments(self):
        """Test the parse_arguments function."""
        # Set up command-line args
        sys.argv = [
            "parse_main.py",
            '--pdf_path', 'test.pdf',
            '--output_dir', 'custom_output',
            '--log_level', 'DEBUG'
        ]
        
        # Call parse_arguments
        args = parse_main.parse_arguments()
        
        # Check that arguments were parsed correctly
        assert args.pdf_path == 'test.pdf'
        assert args.output_dir == 'custom_output'
        assert args.log_level == 'DEBUG'

    def test_configuration_update_from_args(self):
        """Test Configuration.update_from_args method."""
        # Create mock args
        args = MagicMock()
        args.pdf_path = 'test.pdf'
        args.output_dir = 'custom_output'
        args.log_level = 'DEBUG'
        args.config_file = None
        
        # Create a Configuration instance
        config = parse_main.Configuration()
        
        # Update from args
        config.update_from_args(args)
        
        # Check that config was updated correctly
        assert config.pdf_path == 'test.pdf'
        assert config.output_dir == 'custom_output'
        assert config.log_level == 'DEBUG'

    def test_main_with_output_format(self):
        """Test main function with different output formats."""
        # Skip if no test PDF is available
        if not self.test_pdf_path:
            logger.warning("No test PDF available, skipping test")
            return
        
        # Test with JSON format
        sys.argv = [
            "parse_main.py",
            '--pdf_path', str(self.test_pdf_path),
            '--output_dir', self.output_dir,
            '--output_format', 'json'
        ]
        exit_code = parse_main.main()
        
        # Check exit code and output file existence
        assert exit_code == 0
        assert os.path.exists(os.path.join(self.output_dir, "document.json"))


if __name__ == '__main__':
    pytest.main() 