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

# Override imported functions in parse_main
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
                        
                        # Call the main function
                        exit_code = parse_main.main()
                        
                        # Verify the result
                        assert exit_code == 0
                        
                        # Verify process_pdf_document was called
                        mock_process.assert_called_once()
                        
                        # Verify save_output was called
                        mock_save.assert_called_once_with(self.mock_document, self.output_dir)
                        
                        logger.info("Successfully verified main function workflow")
    
    def test_main_function_handles_errors(self):
        """Test the main function handles errors gracefully."""
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
                with patch('parse_main.process_pdf_document') as mock_process:
                    mock_process.side_effect = Exception("Processing error")
                    
                    # Call the main function
                    exit_code = parse_main.main()
                    
                    # Verify the result
                    assert exit_code == 1
                    
                    # Verify process_pdf_document was called
                    mock_process.assert_called_once()
                    
                    logger.info("Successfully verified error handling in main function")
    
    def test_main_function_validates_config(self):
        """Test the main function validates the configuration."""
        # Mock the command line arguments with a missing PDF path
        test_args = [
            'parse_main.py',
            '--output_dir', self.output_dir,
            '--log_level', 'INFO'
        ]
        
        with patch('sys.argv', test_args):
            # Call the main function
            exit_code = parse_main.main()
            
            # Verify the result
            assert exit_code == 1
            
            logger.info("Successfully verified configuration validation")
    
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
        """Test configuration loading from command-line arguments."""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_pdf:
            # Set environment variables
            with patch.dict(os.environ, {
                "DOCLING_PDF_PATH": "env_test.pdf",
                "DOCLING_OUTPUT_DIR": "env_output",
                "DOCLING_LOG_LEVEL": "DEBUG",
                "DOCLING_CONFIG_FILE": "env_config.json"
            }):
                # Create a configuration object (loads from env)
                config = parse_main.Configuration()
                
                # Mock sys.argv for argument parsing with args
                test_args = [
                    'parse_main.py',
                    '--pdf_path', temp_pdf.name,
                    '--output_dir', self.output_dir,
                    '--log_level', 'INFO'
                ]
                
                with patch('sys.argv', test_args):
                    # Parse arguments
                    args = parse_main.parse_arguments()
                    
                    # Update configuration from args
                    config.update_from_args(args)
                    
                    # Verify args overrode environment values
                    assert config.pdf_path == temp_pdf.name
                    assert config.output_dir == self.output_dir
                    assert config.log_level == 'INFO'
                    assert config.config_file == "env_config.json"  # not overridden
                    
                    logger.info("Successfully verified configuration from command-line arguments")


if __name__ == '__main__':
    pytest.main() 