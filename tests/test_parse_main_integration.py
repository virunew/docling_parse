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
import re
import subprocess

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
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        # Create a test output directory
        cls.test_output_dir = Path("tests/integration_output")
        cls.test_output_dir.mkdir(exist_ok=True, parents=True)
        
        # We'll need a sample PDF for testing
        # For this test, we'll check if a sample file exists or skip the test
        cls.sample_pdf_file = None
        for path in [
            "sample.pdf",
            "tests/sample.pdf",
            "tests/data/sample.pdf"
        ]:
            if Path(path).exists():
                cls.sample_pdf_file = path
                break
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        # Remove the test output directory
        if cls.test_output_dir.exists():
            shutil.rmtree(cls.test_output_dir)
    
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

    def test_parse_main_output_files(self):
        """Test that parse_main.py creates output files without base64 data"""
        if not self.sample_pdf_file:
            self.skipTest("Sample PDF file not found for testing")
        
        # Run parse_main.py with the sample PDF
        command = [
            "python", "parse_main.py",
            "--pdf_path", self.sample_pdf_file,
            "--output_dir", str(self.test_output_dir)
        ]
        
        # Print the command for debugging
        print(f"Running: {' '.join(command)}")
        
        # Run the command and get the result
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            print(f"Command stdout: {result.stdout}")
            print(f"Command stderr: {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"Command failed with code {e.returncode}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            self.fail(f"parse_main.py failed with error code {e.returncode}")
        
        # Check for the fixed_document.json file
        fixed_document_file = self.test_output_dir / "fixed_document.json"
        self.assertTrue(fixed_document_file.exists(), 
                        f"fixed_document.json not found in {self.test_output_dir}")
        
        # Load the fixed document JSON
        with open(fixed_document_file, 'r', encoding='utf-8') as f:
            fixed_document = json.load(f)
        
        # Check if the JSON contains any base64 data
        document_json_str = json.dumps(fixed_document)
        
        # Pattern to detect base64 data in data URIs
        base64_pattern = r'data:image\/[^;]+;base64,[A-Za-z0-9+/]+'
        
        # Find all matches of base64 data
        base64_matches = re.findall(base64_pattern, document_json_str)
        
        # There should be no base64 data in the fixed document
        self.assertEqual(len(base64_matches), 0, 
                        f"Found {len(base64_matches)} base64 data URIs in fixed_document.json")
        
        # Check other output files if they exist (e.g., formatted output)
        for json_file in self.test_output_dir.glob("*.json"):
            if json_file != fixed_document_file:
                print(f"Checking {json_file}")
                with open(json_file, 'r', encoding='utf-8') as f:
                    try:
                        json_content = json.load(f)
                        json_str = json.dumps(json_content)
                        base64_matches = re.findall(base64_pattern, json_str)
                        self.assertEqual(len(base64_matches), 0, 
                                        f"Found {len(base64_matches)} base64 data URIs in {json_file}")
                    except json.JSONDecodeError:
                        print(f"Warning: Could not parse {json_file} as JSON")
        
        # Check if image files were created
        doc_id = Path(self.sample_pdf_file).stem
        images_dir = self.test_output_dir / doc_id / "images"
        
        if images_dir.exists():
            image_files = list(images_dir.glob("*.*"))
            print(f"Found {len(image_files)} image files in {images_dir}")
            
            # If there are pictures in the document, there should be image files
            if "pictures" in fixed_document and fixed_document["pictures"]:
                self.assertGreater(len(image_files), 0, 
                                f"No image files found in {images_dir} despite pictures in document")


def main():
    """Run the tests."""
    unittest.main()


if __name__ == "__main__":
    main() 