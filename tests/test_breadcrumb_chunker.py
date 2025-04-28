import unittest
from pathlib import Path
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from breadcrumb_chunker import BreadcrumbChunker

# Update the import statements to match the working example
from docling.document_converter import DocumentConverter
from docling.document_converter import PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

class TestBreadcrumbChunker(unittest.TestCase):
    """Tests for the BreadcrumbChunker implementation."""

    def setUp(self):
        """Set up test environment."""
        # Define the path to your test PDF - adjust as needed
        self.test_pdf_path = Path('/Users/tech9/work/nipl/ItemExtraction/SBW_AI sample page10-11.pdf')
        
        # Skip the test if the file doesn't exist
        if not self.test_pdf_path.exists():
            self.skipTest(f"Test PDF not found at {self.test_pdf_path}")
            
        # Configure the document converter
        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = 2.0
        pipeline_options.generate_page_images = True
        pipeline_options.generate_picture_images = True
        pipeline_options.do_ocr = False
        
        # Initialize the converter
        self.doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        # Convert the document
        self.conv_res = self.doc_converter.convert(self.test_pdf_path)
        
        # Create the chunker
        self.chunker = BreadcrumbChunker(merge_list_items=True)

    def test_breadcrumb_creation(self):
        """Test that breadcrumbs are properly created with full hierarchy."""
        # Process the document and collect chunks
        chunks = list(self.chunker.chunk(self.conv_res.document))
        
        # Create a dictionary of texts to breadcrumbs for easier testing
        text_to_breadcrumb = {chunk.text: chunk.meta.headings for chunk in chunks}
        
        # Test specific cases
        
        # The "Shall" text should have a breadcrumb containing the full hierarchy
        shall_text = "The word \"shall\" be used to state a binding requirement. Such requirements are externally verifiable by manipulation or observation."
        self.assertIn(shall_text, text_to_breadcrumb)
        shall_breadcrumb = text_to_breadcrumb[shall_text]
        
        # Check that the breadcrumb contains all levels
        self.assertIsNotNone(shall_breadcrumb)
        self.assertIn("3.2.2. Definitions", shall_breadcrumb)
        self.assertIn("3.2.2.1. Obligation of Requirement Wording", shall_breadcrumb)
        self.assertIn("Shall", shall_breadcrumb)
        
        # Verify it has the correct structure (should be "3.2.2. Definitions > 3.2.2.1. Obligation of Requirement Wording > Shall")
        expected_structure = "3.2.2. Definitions > 3.2.2.1. Obligation of Requirement Wording > Shall"
        self.assertEqual(shall_breadcrumb, expected_structure)
        
        # Similarly check for "Should" and "May"
        should_text = "The word \"should\" be used for preferences in implementation that are not strictly binding."
        may_text = "The word \"may\" be used to denote options that are left to the implementer."
        
        # Verify "Should" breadcrumb
        should_breadcrumb = text_to_breadcrumb.get(should_text)
        self.assertIsNotNone(should_breadcrumb)
        self.assertEqual(should_breadcrumb, "3.2.2. Definitions > 3.2.2.1. Obligation of Requirement Wording > Should")
        
        # Verify "May" breadcrumb
        may_breadcrumb = text_to_breadcrumb.get(may_text)
        self.assertIsNotNone(may_breadcrumb)
        self.assertEqual(may_breadcrumb, "3.2.2. Definitions > 3.2.2.1. Obligation of Requirement Wording > May")

if __name__ == '__main__':
    unittest.main() 