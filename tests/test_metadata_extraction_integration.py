#!/usr/bin/env python3
"""
Integration Tests for Metadata Extraction

This module contains integration tests for metadata extraction functionality,
verifying that metadata is correctly extracted, processed, and integrated
with the rest of the application components.
"""

import unittest
import json
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Ensure src directory is in the Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

# Import the functionality to test
from parse_main_new import main
from parse_helper import process_pdf_document, save_output 
from metadata_extractor import (
    convert_bbox,
    extract_page_number,
    extract_image_metadata,
    build_metadata_object,
    extract_full_metadata
)

class TestMetadataExtractionIntegration(unittest.TestCase):
    """Integration tests for metadata extraction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for output
        self.temp_dir = tempfile.mkdtemp()
        
        # Path to test PDF file (need to create or mock)
        self.test_pdf_path = self._get_test_pdf_path()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory and all its contents
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _get_test_pdf_path(self):
        """Get path to test PDF file."""
        # Look for a test PDF in common locations
        test_paths = [
            # Test file in tests directory
            Path(__file__).resolve().parent / 'test_data' / 'sample.pdf',
            # Test file in project root
            Path(__file__).resolve().parent.parent / 'test_data' / 'sample.pdf',
            # Test file in src directory
            Path(__file__).resolve().parent.parent / 'src' / 'test_data' / 'sample.pdf'
        ]
        
        for path in test_paths:
            if path.exists():
                return str(path)
        
        # If no test PDF found, just return a placeholder (tests will be skipped)
        return "test_data/sample.pdf"
    
    def test_process_pdf_with_metadata_extraction(self):
        """Test processing a PDF document with metadata extraction."""
        # Skip test if no test PDF file is available
        if not Path(self.test_pdf_path).exists():
            self.skipTest(f"Test PDF file not found: {self.test_pdf_path}")
        
        try:
            # Process the test PDF
            document = process_pdf_document(self.test_pdf_path, self.temp_dir)
            
            # Check that the document was processed successfully
            self.assertIsNotNone(document)
            
            # Check that element map with metadata was created
            doc_name = getattr(document, 'name', 'docling_document')
            metadata_map_path = Path(self.temp_dir) / doc_name / "element_map_with_metadata.json"
            
            self.assertTrue(metadata_map_path.exists())
            
            # Load the element map with metadata
            with open(metadata_map_path, 'r', encoding='utf-8') as f:
                element_map = json.load(f)
            
            # Verify that metadata was added to elements
            if 'flattened_sequence' in element_map:
                has_metadata = False
                for element in element_map['flattened_sequence']:
                    if 'extracted_metadata' in element:
                        has_metadata = True
                        # Verify basic metadata fields
                        metadata = element['extracted_metadata']
                        self.assertIn('coords_x', metadata)
                        self.assertIn('coords_y', metadata)
                        self.assertIn('coords_cx', metadata)
                        self.assertIn('coords_cy', metadata)
                        self.assertIn('master_index', metadata)
                        
                        # Also check that metadata.metadata exists with more detailed info
                        self.assertIn('metadata', metadata)
                        self.assertIn('breadcrumb', metadata['metadata'])
                        
                        # If there's at least one element with metadata, that's sufficient
                        break
                
                self.assertTrue(has_metadata, "No elements found with extracted metadata")
            else:
                self.fail("No flattened_sequence found in element map")
                
        except Exception as e:
            self.fail(f"Error during test: {e}")
    
    def test_convert_bbox_integration(self):
        """Test convert_bbox function integration with document processing."""
        # Create a sample bounding box
        bbox = {
            "l": 56.7,
            "t": 115.2,
            "r": 555.3,
            "b": 309.8
        }
        
        # Convert the bounding box
        converted = convert_bbox(bbox)
        
        # Verify the conversion results
        self.assertEqual(converted["coords_x"], 56)
        self.assertEqual(converted["coords_y"], 115)
        self.assertEqual(converted["coords_cx"], 498)
        self.assertEqual(converted["coords_cy"], 194)
        
        # Verify conversion with float values
        converted_float = convert_bbox(bbox, to_integers=False)
        self.assertIsInstance(converted_float["coords_x"], float)
        self.assertIsInstance(converted_float["coords_y"], float)
        self.assertIsInstance(converted_float["coords_cx"], float)
        self.assertIsInstance(converted_float["coords_cy"], float)
    
    def test_extract_full_metadata_integration(self):
        """Test extract_full_metadata with sample element and sequence."""
        # Create sample element and sequence
        element = {
            "id": "text_1",
            "self_ref": "#/texts/0",
            "text": "Sample text",
            "prov": {
                "page_no": 2,
                "bbox": {
                    "l": 100,
                    "t": 200,
                    "r": 300,
                    "b": 250
                }
            }
        }
        
        sequence = [
            {
                "id": "header_1",
                "self_ref": "#/texts/1",
                "text": "Document Title",
                "metadata": {"type": "h1"}
            },
            element
        ]
        
        doc_info = {
            "filename": "test.pdf",
            "mimetype": "application/pdf"
        }
        
        # Extract full metadata
        metadata = extract_full_metadata(element, sequence, doc_info)
        
        # Verify metadata fields
        self.assertEqual(metadata["coords_x"], 100)
        self.assertEqual(metadata["coords_y"], 200)
        self.assertEqual(metadata["coords_cx"], 200)
        self.assertEqual(metadata["coords_cy"], 50)
        self.assertEqual(metadata["master_index"], 2)
        self.assertEqual(metadata["file_type"], "application/pdf")
        self.assertEqual(metadata["file_source"], "test.pdf")
        
        # Verify metadata.metadata
        self.assertIn("metadata", metadata)
        self.assertIn("breadcrumb", metadata["metadata"])
        self.assertEqual(metadata["metadata"]["breadcrumb"], "Document Title")
        self.assertEqual(metadata["metadata"]["page_no"], 2)

if __name__ == "__main__":
    unittest.main() 