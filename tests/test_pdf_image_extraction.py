#!/usr/bin/env python3
"""
Test PDF Image Extraction

This script tests the integration of the PDFImageExtractor with the main parsing flow.
It verifies that images can be extracted from PDF documents and properly integrated
into the output JSON.
"""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path
import unittest

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the modules to test
from save_output import save_output
from src.parse_main import process_pdf_document
from src.pdf_image_extractor import PDFImageExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPDFImageExtraction(unittest.TestCase):
    """Test suite for PDF image extraction functionality."""
    
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
        
        # Skip if the test file doesn't exist
        if not Path(self.sample_pdf_path).exists():
            self.skipTest(f"Test PDF file not found: {self.sample_pdf_path}")
    
    def tearDown(self):
        """Clean up after the test."""
        self.temp_dir.cleanup()
    
    def test_pdf_image_extractor(self):
        """Test the PDFImageExtractor class directly."""
        # Skip if the test file doesn't exist
        if not Path(self.sample_pdf_path).exists():
            self.skipTest(f"Test PDF file not found: {self.sample_pdf_path}")
        
        # Create an instance of PDFImageExtractor
        config = {
            'images_scale': 2.0,
            'do_picture_description': True,
        }
        extractor = PDFImageExtractor(config)
        
        # Extract images from the PDF
        images_data = extractor.extract_images(self.sample_pdf_path)
        
        # Verify that we got a valid dictionary
        self.assertIsInstance(images_data, dict)
        self.assertIn("document_name", images_data)
        self.assertIn("total_pages", images_data)
        self.assertIn("images", images_data)
        
        # Log info about extracted images
        logger.info(f"Extracted {len(images_data['images'])} images from {self.sample_pdf_path}")
    
    def test_integrated_extraction(self):
        """Test the integration of PDFImageExtractor with the main parsing flow."""
        # Skip if the test file doesn't exist
        if not Path(self.sample_pdf_path).exists():
            self.skipTest(f"Test PDF file not found: {self.sample_pdf_path}")
        
        # Process the PDF document
        docling_document = process_pdf_document(
            self.sample_pdf_path, 
            self.output_dir
        )
        
        # Verify that the document was processed
        self.assertIsNotNone(docling_document)
        
        # Save the output
        output_file = save_output(docling_document, self.output_dir)
        
        # Verify that the output file exists
        self.assertTrue(output_file.exists())
        
        # Load the output JSON
        with open(output_file, 'r', encoding='utf-8') as f:
            doc_dict = json.load(f)
        
        # Verify that 'images_data' is in the output (if images were found)
        images_data_file = self.output_dir / "images_data.json"
        if images_data_file.exists():
            self.assertIn("images_data", doc_dict)
            logger.info(f"Found {len(doc_dict['images_data']['images'])} images in output JSON")
        
        # Verify that the 'images' directory exists if images were extracted
        images_dir = self.output_dir / "images"
        if images_dir.exists():
            image_files = list(images_dir.glob("*"))
            logger.info(f"Found {len(image_files)} image files in {images_dir}")


def main():
    """Run the tests."""
    unittest.main()


if __name__ == "__main__":
    main() 