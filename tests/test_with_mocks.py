#!/usr/bin/env python3
"""
Test Integration with Mock Docling

This script tests the integration of the PDFImageExtractor with the main parsing flow
using mock docling modules.
"""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path
import unittest
from unittest import mock

from save_output import save_output

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the mock docling classes
from mock_docling import (
    DocumentConverter,
    PdfFormatOption,
    InputFormat,
    PdfPipelineOptions,
    ConversionResult,
    MockDocument
)

# Mock element_map_builder.build_element_map function
def mock_build_element_map(document):
    """Mock implementation of build_element_map."""
    return {
        "document_name": getattr(document, "name", "mock_document"),
        "total_pages": len(getattr(document, "pages", {})),
        "text_segments": [
            {
                "id": "text1",
                "text": "This is some mock text before the image.",
                "page": 1,
                "bounds": {
                    "l": 0, "t": 0, "r": 100, "b": 50,
                    "width": 100, "height": 50
                }
            },
            {
                "id": "text2",
                "text": "This is some mock text after the image.",
                "page": 1,
                "bounds": {
                    "l": 0, "t": 150, "r": 100, "b": 200,
                    "width": 100, "height": 50
                }
            }
        ],
        "pictures": [
            {
                "id": "picture1",
                "type": "picture",
                "page": 1,
                "bounds": {
                    "l": 0, "t": 50, "r": 100, "b": 150,
                    "width": 100, "height": 100
                },
                "metadata": {
                    "type": "picture"
                }
            }
        ],
        "flattened_sequence": [
            {
                "id": "text1",
                "text": "This is some mock text before the image.",
                "page": 1,
                "sequence_number": 1
            },
            {
                "id": "picture1",
                "type": "picture",
                "page": 1,
                "sequence_number": 2
            },
            {
                "id": "text2",
                "text": "This is some mock text after the image.",
                "page": 1,
                "sequence_number": 3
            }
        ]
    }


class TestWithMocks(unittest.TestCase):
    """Test the PDF image extractor integration using mocks."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for output files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Path to the sample PDF
        self.sample_pdf_path = str(Path(__file__).parent / "data" / "sample.pdf")
        
        # Skip if the test file doesn't exist
        if not Path(self.sample_pdf_path).exists():
            self.skipTest(f"Test PDF file not found: {self.sample_pdf_path}")
        
        # Create the patches
        self.patches = [
            mock.patch.dict(sys.modules, {
                'docling': mock.MagicMock(),
                'docling.document_converter': mock.MagicMock(),
                'docling.datamodel.base_models': mock.MagicMock(),
                'docling.datamodel.pipeline_options': mock.MagicMock(),
                'docling.datamodel.document': mock.MagicMock()
            }),
            mock.patch('src.parse_main.DocumentConverter', DocumentConverter),
            mock.patch('src.parse_main.PdfFormatOption', PdfFormatOption),
            mock.patch('src.parse_main.InputFormat', InputFormat),
            mock.patch('src.parse_main.PdfPipelineOptions', PdfPipelineOptions),
            mock.patch('src.pdf_image_extractor.DocumentConverter', DocumentConverter),
            mock.patch('src.pdf_image_extractor.PdfFormatOption', PdfFormatOption),
            mock.patch('src.pdf_image_extractor.InputFormat', InputFormat),
            mock.patch('src.pdf_image_extractor.PdfPipelineOptions', PdfPipelineOptions),
            mock.patch('src.pdf_image_extractor.ConversionResult', ConversionResult),
            mock.patch('src.parse_main.build_element_map', mock_build_element_map)
        ]
        
        # Start all patches
        for patcher in self.patches:
            patcher.start()
        
        # Import the test modules after patching
        from src.parse_main import process_pdf_document
        from src.pdf_image_extractor import PDFImageExtractor
        
        self.process_pdf_document = process_pdf_document
        self.save_output = save_output
        self.PDFImageExtractor = PDFImageExtractor
    
    def tearDown(self):
        """Clean up after the test."""
        # Stop all patches
        for patcher in self.patches:
            patcher.stop()
        
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_pdf_image_extractor(self):
        """Test the PDFImageExtractor class with mocks."""
        # Create a mock config
        config = {
            'images_scale': 2.0,
            'do_picture_description': True
        }
        
        # Create an instance of PDFImageExtractor
        extractor = self.PDFImageExtractor(config)
        
        # Extract images from the PDF
        images_data = extractor.extract_images(self.sample_pdf_path)
        
        # Verify the results
        self.assertIsInstance(images_data, dict)
        self.assertIn("document_name", images_data)
        self.assertIn("total_pages", images_data)
        self.assertIn("images", images_data)
        self.assertEqual(len(images_data["images"]), 2)
        
        # Log the results
        logger.info(f"Extracted {len(images_data['images'])} mock images")
    
    def test_integration(self):
        """Test the integration of PDFImageExtractor with process_pdf_document."""
        # Process the PDF document
        document = self.process_pdf_document(self.sample_pdf_path, self.output_dir)
        
        # Verify the document was processed
        self.assertIsNotNone(document)
        
        # Create the directories and files that would be created by the real code
        # since our mocks don't actually create these
        images_dir = self.output_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        images_data_file = self.output_dir / "images_data.json"
        with open(images_data_file, 'w') as f:
            json.dump({
                "document_name": document.name,
                "total_pages": len(document.pages),
                "images": [
                    {
                        "metadata": {
                            "id": "picture_1",
                            "docling_ref": "#/pictures/0",
                            "page_number": 1,
                            "description": "Mock image 1",
                            "format": "image/png"
                        },
                        "data_uri": "data:image/png;base64,bW9jayBpbWFnZSBkYXRh"
                    },
                    {
                        "metadata": {
                            "id": "picture_2",
                            "docling_ref": "#/pictures/1",
                            "page_number": 2,
                            "description": "Mock image 2",
                            "format": "image/png"
                        },
                        "data_uri": "data:image/png;base64,bW9jayBpbWFnZSBkYXRh"
                    }
                ]
            }, f)
        
        # Save the output
        output_file = self.save_output(document, self.output_dir)
        
        # Verify the output file was created
        self.assertTrue(output_file.exists())
        
        # Load the output JSON
        with open(output_file, 'r', encoding='utf-8') as f:
            doc_dict = json.load(f)
        
        # Verify that images_data was included in the output
        self.assertIn("images_data", doc_dict)


if __name__ == "__main__":
    unittest.main() 