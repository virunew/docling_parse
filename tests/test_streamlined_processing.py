#!/usr/bin/env python3
"""
Test the streamlined processing functionality to ensure it produces the same output as the original.
"""

import unittest
import os
import json
import shutil
from pathlib import Path
import tempfile
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)

# Allow imports relative to project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from parse_helper import process_pdf_document, save_output
from src.json_metadata_fixer import fix_metadata
from src.utils import replace_base64_with_file_references
from output_formatter import OutputFormatter
from src.streamlined_processor import streamlined_process


class StreamlinedProcessingTest(unittest.TestCase):
    """Test suite for the streamlined processing implementation."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for testing
        self.temp_dir_original = tempfile.mkdtemp()
        self.temp_dir_streamlined = tempfile.mkdtemp()
        
        # Set up test data paths
        self.test_data_dir = Path(__file__).parent / "data"
        self.sample_pdf_path = self.test_data_dir / "sample.pdf"
        
        # Create test data directory if it doesn't exist
        self.test_data_dir.mkdir(exist_ok=True, parents=True)
        
        # Skip test setup if no sample PDF exists and note we need one
        if not self.sample_pdf_path.exists():
            print(f"\nWARNING: Sample PDF not found at {self.sample_pdf_path}")
            print(f"Please add a sample PDF at this location for complete testing")
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directories
        shutil.rmtree(self.temp_dir_original, ignore_errors=True)
        shutil.rmtree(self.temp_dir_streamlined, ignore_errors=True)
    
    def test_streamlined_output_equivalence(self):
        """Test that streamlined process produces equivalent output to original process."""
        # Skip test if sample PDF doesn't exist
        if not self.sample_pdf_path.exists():
            self.skipTest(f"Sample PDF not found at {self.sample_pdf_path}")
        
        # Common formatter configuration
        formatter_config = {
            'include_metadata': True,
            'include_images': True,
            'image_base_url': '',
            'include_page_breaks': True,
            'include_captions': True
        }
        
        # ------- ORIGINAL PROCESS -------
        # Process with original method
        docling_document = process_pdf_document(
            str(self.sample_pdf_path), 
            self.temp_dir_original, 
            None
        )
        
        # Save the output as JSON (standard format)
        output_file = save_output(docling_document, self.temp_dir_original)
        
        # Load the JSON output for formatting
        with open(output_file, 'r', encoding='utf-8') as f:
            document_data = json.load(f)
        
        # Apply metadata fixes
        fixed_document_data = fix_metadata(document_data, self.temp_dir_original)
        
        # Replace base64 image data with file references
        doc_id = self.sample_pdf_path.stem
        fixed_document_data_for_storage = replace_base64_with_file_references(
            fixed_document_data, 
            Path(self.temp_dir_original),
            doc_id
        )
        
        # Save formatted output
        formatter = OutputFormatter(formatter_config)
        original_output_file = formatter.save_formatted_output(
            fixed_document_data_for_storage,
            self.temp_dir_original,
            "json"
        )
        
        # ------- STREAMLINED PROCESS -------
        # Process with streamlined method
        streamlined_output_file = streamlined_process(
            docling_document,
            self.temp_dir_streamlined,
            str(self.sample_pdf_path),
            formatter_config,
            "json"
        )
        
        # ------- COMPARISON -------
        # Load both JSON files
        with open(original_output_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        with open(streamlined_output_file, 'r', encoding='utf-8') as f:
            streamlined_data = json.load(f)
        
        # Compare the essential structures
        self.assertEqual(
            original_data.keys(), 
            streamlined_data.keys(),
            "Output JSON keys differ between original and streamlined processes"
        )
        
        # Check for 'chunks' key specifically
        if 'chunks' in original_data and 'chunks' in streamlined_data:
            self.assertEqual(
                len(original_data['chunks']),
                len(streamlined_data['chunks']),
                "Number of chunks differs between original and streamlined processes"
            )
            
            # Compare a few key attributes if chunks exist
            if len(original_data['chunks']) > 0:
                first_orig_chunk = original_data['chunks'][0]
                first_stream_chunk = streamlined_data['chunks'][0]
                
                # Check essential fields
                self.assertEqual(
                    first_orig_chunk.get('content_type'),
                    first_stream_chunk.get('content_type'),
                    "Content type field differs in first chunk"
                )
                
                self.assertEqual(
                    first_orig_chunk.get('master_index'),
                    first_stream_chunk.get('master_index'),
                    "Page number (master_index) differs in first chunk"
                )
        
        # Check for images directory
        original_images_dir = Path(self.temp_dir_original) / "images"
        streamlined_images_dir = Path(self.temp_dir_streamlined) / "images"
        
        if original_images_dir.exists():
            self.assertTrue(
                streamlined_images_dir.exists(),
                "Streamlined process did not create images directory when original process did"
            )
            
            # Get image file counts
            original_image_count = len(list(original_images_dir.glob('*')))
            streamlined_image_count = len(list(streamlined_images_dir.glob('*')))
            
            self.assertEqual(
                original_image_count,
                streamlined_image_count,
                "Number of image files differs between original and streamlined processes"
            )
        elif streamlined_images_dir.exists():
            self.fail("Streamlined process created images directory when original process did not")
        

if __name__ == '__main__':
    unittest.main() 