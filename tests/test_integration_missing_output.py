"""
Integration test to verify that parse_main.py correctly handles image_extraction_config parameter
and generates the standardized output file.
"""
import os
import sys
import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

# Mock docling and related modules before importing our code
sys.modules['docling'] = MagicMock()
sys.modules['docling.docling'] = MagicMock()
sys.modules['docling.docling.document_converter'] = MagicMock()
sys.modules['docling.docling.datamodel'] = MagicMock()
sys.modules['docling.docling.datamodel.base_models'] = MagicMock()
sys.modules['docling.docling.datamodel.pipeline_options'] = MagicMock()
sys.modules['docling.docling.document_converter.DocumentConverter'] = MagicMock()
sys.modules['docling.docling.datamodel.base_models.InputFormat'] = MagicMock()
sys.modules['docling.docling.document_converter.PdfFormatOption'] = MagicMock()
sys.modules['docling.docling.datamodel.pipeline_options.PdfPipelineOptions'] = MagicMock()
sys.modules['docling_fix'] = MagicMock()
sys.modules['docling_integration'] = MagicMock()
sys.modules['element_map_builder'] = MagicMock()
sys.modules['pdf_image_extractor'] = MagicMock()
sys.modules['image_extraction_module'] = MagicMock()
sys.modules['metadata_extractor'] = MagicMock()
sys.modules['output_formatter'] = MagicMock()
sys.modules['format_standardized_output'] = MagicMock()
sys.modules['logger_config'] = MagicMock()
sys.modules['content_extractor'] = MagicMock()

# Create a mock SQLFormatter class
mock_sql_formatter = MagicMock()
mock_sql_formatter.SQLFormatter = MagicMock()
sys.modules['src.sql_formatter'] = mock_sql_formatter

# Add project root to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import the modules to test
from parse_main import main, Configuration


class TestIntegrationMissingOutput(unittest.TestCase):
    """Test that parse_main.py correctly generates all required output files."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # We'll use a small sample file for our test
        self.test_file = os.path.join("tests", "data", "sample_document.pdf")
        
        # If the test file doesn't exist, create a dummy file
        if not os.path.exists(self.test_file):
            os.makedirs(os.path.dirname(self.test_file), exist_ok=True)
            with open(self.test_file, 'wb') as f:
                f.write(b'%PDF-1.4\n%%EOF')
    
    def tearDown(self):
        """Clean up the test environment."""
        self.temp_dir.cleanup()
    
    @patch('parse_main.process_pdf_document')
    @patch('parse_main.save_output')
    @patch('parse_main.OutputFormatter')
    @patch('parse_main.save_standardized_output')
    @patch('parse_main.setup_logging')
    def test_all_output_files_generated(self, 
                                    mock_setup_logging,
                                    mock_save_standardized_output, 
                                    mock_output_formatter, 
                                    mock_save_output, 
                                    mock_process_pdf_document):
        """Test that all output files are generated correctly."""
        # Set up mocks
        mock_doc = MagicMock()
        mock_doc.name = "sample_document"
        mock_process_pdf_document.return_value = mock_doc
        
        mock_output_file = os.path.join(self.output_dir, "sample_document.json")
        mock_save_output.return_value = mock_output_file
        
        mock_formatter_instance = MagicMock()
        mock_output_formatter.return_value = mock_formatter_instance
        mock_formatted_output_file = os.path.join(self.output_dir, "sample_document_formatted.json")
        mock_formatter_instance.save_formatted_output.return_value = mock_formatted_output_file
        
        mock_standardized_output_file = os.path.join(self.output_dir, "sample_document_standardized.json")
        mock_save_standardized_output.return_value = mock_standardized_output_file
        
        # Create a dummy JSON file for the formatter to read
        os.makedirs(self.output_dir, exist_ok=True)
        with open(mock_output_file, 'w') as f:
            json.dump({"name": "sample_document"}, f)
        
        # Patch argv to provide command-line arguments
        with patch('sys.argv', ['parse_main.py', 
                               f'--pdf_path={self.test_file}', 
                               f'--output_dir={self.output_dir}',
                               '--output_format=json']):
            # Call the main function
            exit_code = main()
            
            # Verify it completed successfully
            self.assertEqual(exit_code, 0)
            
            # Verify that process_pdf_document was called with the correct image_extraction_config
            args, kwargs = mock_process_pdf_document.call_args
            self.assertIn('image_extraction_config', kwargs)
            self.assertIsInstance(kwargs['image_extraction_config'], dict)
            
            # Verify that all output files were generated
            mock_save_output.assert_called_once()
            mock_formatter_instance.save_formatted_output.assert_called_once()
            mock_save_standardized_output.assert_called_once()
            
            # Verify that the standardized output file was created (using ANY for the output_dir which may be 
            # passed as a string or Path object)
            mock_save_standardized_output.assert_called_with(
                {"name": "sample_document"},  # The document data
                ANY,                          # The output directory (may be string or Path object)
                self.test_file                # The input PDF path
            )
    
    @patch('parse_main.setup_logging')
    def test_configuration_get_image_extraction_config(self, mock_setup_logging):
        """Test that the Configuration class correctly provides image extraction config."""
        # Create a configuration with custom image settings
        config = Configuration()
        config.extract_images = True
        config.image_scale_factor = 3.0
        config.image_min_size = 200
        config.process_images_in_parallel = True
        config.image_format = "PNG"
        config.image_quality = 90
        
        # Get the image extraction config
        image_config = config.get_image_extraction_config()
        
        # Verify it contains the expected values
        self.assertTrue(image_config['extract_images'])
        self.assertEqual(image_config['image_scale_factor'], 3.0)
        self.assertEqual(image_config['image_min_size'], 200)
        self.assertTrue(image_config['process_images_in_parallel'])
        self.assertEqual(image_config['image_format'], "PNG")
        self.assertEqual(image_config['image_quality'], 90)


if __name__ == '__main__':
    unittest.main() 