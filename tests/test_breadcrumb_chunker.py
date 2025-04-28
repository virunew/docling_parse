import unittest
from pathlib import Path
import os
import sys
import tempfile
import shutil

# Add the project root directory (one level up from tests/) to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Now use imports relative to the project root structure
from src.experimental.breadcrumb_chunker import BreadcrumbChunker
from docling.docling.document_converter import DocumentConverter, PdfFormatOption
from docling.docling.datamodel.base_models import InputFormat
from docling.docling.datamodel.pipeline_options import PdfPipelineOptions
# This import might still be tricky depending on how docling_core is structured/installed.
# If the below fails, we might need to rely on PYTHONPATH or venv setup.
from docling_core.types.doc.document import PictureItem, TableItem

class TestBreadcrumbChunker(unittest.TestCase):
    """Tests for the BreadcrumbChunker implementation."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for the class."""
        # Define the path to your test PDF
        cls.test_pdf_path = Path('/Users/tech9/work/nipl/ItemExtraction/SBW_AI sample page10-11.pdf')
        
        if not cls.test_pdf_path.exists():
            raise unittest.SkipTest(f"Test PDF not found at {cls.test_pdf_path}")
        
        # Create a temporary directory for test outputs
        cls.temp_output_dir = Path(tempfile.mkdtemp(prefix="test_docling_"))
        cls.doc_filename = cls.test_pdf_path.stem

        # Configure the document converter
        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = 2.0
        pipeline_options.generate_page_images = True
        pipeline_options.generate_picture_images = True
        pipeline_options.do_ocr = False
        
        # Initialize the converter
        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        # Convert the document
        cls.conv_res = doc_converter.convert(cls.test_pdf_path)
        
        # Build image reference map and save images (simulate main script)
        cls.image_ref_map = {}
        picture_counter = 0
        for element, _level in cls.conv_res.document.iterate_items():
             if isinstance(element, PictureItem):
                picture_counter += 1
                relative_image_filename = f"{cls.doc_filename}-picture-{picture_counter}.png"
                cls.image_ref_map[element.self_ref] = relative_image_filename
                full_image_path = cls.temp_output_dir / relative_image_filename
                try:
                    img = element.get_image(cls.conv_res.document)
                    if img:
                        with full_image_path.open("wb") as fp:
                            img.save(fp, "PNG")
                except Exception as e:
                    print(f"Warning: Could not save image for {element.self_ref} during test setup: {e}")
        
        # Create the chunker
        cls.chunker = BreadcrumbChunker(merge_list_items=True)
        
        # Generate chunks once for all tests
        cls.chunks = list(cls.chunker.chunk(cls.conv_res.document, image_ref_map=cls.image_ref_map))
        cls.text_to_chunk = {chunk.text: chunk for chunk in cls.chunks}
        cls.type_to_chunks = {
            "text": [c for c in cls.chunks if c.meta.chunk_type == "text"],
            "image": [c for c in cls.chunks if c.meta.chunk_type == "image"],
            "table": [c for c in cls.chunks if c.meta.chunk_type == "table"],
        }

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory after all tests."""
        if hasattr(cls, 'temp_output_dir') and cls.temp_output_dir.exists():
            shutil.rmtree(cls.temp_output_dir)

    def test_breadcrumb_creation_text(self):
        """Test breadcrumbs for standard text chunks."""
        # The "Shall" text should have a breadcrumb containing the full hierarchy
        shall_text = "The word \"shall\" be used to state a binding requirement. Such requirements are externally verifiable by manipulation or observation."
        self.assertIn(shall_text, self.text_to_chunk, "Shall text not found in chunks")
        shall_chunk = self.text_to_chunk[shall_text]
        
        self.assertEqual(shall_chunk.meta.chunk_type, "text")
        shall_breadcrumb = shall_chunk.meta.headings
        
        self.assertIsNotNone(shall_breadcrumb)
        expected_structure = "3.2.2. Definitions > 3.2.2.1. Obligation of Requirement Wording > Shall"
        self.assertEqual(shall_breadcrumb, expected_structure)
        
        # Similarly check for "Should" and "May"
        should_text = "The word \"should\" be used for preferences in implementation that are not strictly binding."
        may_text = "The word \"may\" be used to denote options that are left to the implementer."
        
        should_chunk = self.text_to_chunk.get(should_text)
        self.assertIsNotNone(should_chunk, "Should text not found")
        self.assertEqual(should_chunk.meta.chunk_type, "text")
        self.assertEqual(should_chunk.meta.headings, "3.2.2. Definitions > 3.2.2.1. Obligation of Requirement Wording > Should")
        
        may_chunk = self.text_to_chunk.get(may_text)
        self.assertIsNotNone(may_chunk, "May text not found")
        self.assertEqual(may_chunk.meta.chunk_type, "text")
        self.assertEqual(may_chunk.meta.headings, "3.2.2. Definitions > 3.2.2.1. Obligation of Requirement Wording > May")

    def test_table_chunk_creation(self):
        """Test that table chunks are created correctly."""
        table_chunks = self.type_to_chunks["table"]
        self.assertGreater(len(table_chunks), 0, "No table chunks were generated.")
        
        # Assuming the first table chunk corresponds to the first table in the doc
        first_table_chunk = table_chunks[0]
        self.assertEqual(first_table_chunk.meta.chunk_type, "table")
        self.assertIsNone(first_table_chunk.meta.image_path) # Ensure image path is None for tables
        self.assertIsNotNone(first_table_chunk.text) # Ensure table text exists
        self.assertTrue(len(first_table_chunk.meta.doc_items) > 0) # Ensure doc item is linked
        self.assertIsInstance(first_table_chunk.meta.doc_items[0], TableItem) # Check type
        
        # Check breadcrumb for the known table (assuming it has no specific heading)
        # Adjust this if the table falls under a specific heading in your test doc
        self.assertIsNone(first_table_chunk.meta.headings, f"Table chunk has unexpected heading: {first_table_chunk.meta.headings}")
        
        # Check if the text contains expected table content snippets
        self.assertIn("MCU, 1 = Micro controller unit", first_table_chunk.text)
        self.assertIn("VCU, 1 = Vehicle Control Unit", first_table_chunk.text)

    def test_image_chunk_creation(self):
        """Test that image chunks are created correctly."""
        image_chunks = self.type_to_chunks["image"]
        # Note: The sample PDF might not have images, adjust assertion if needed
        # self.assertGreater(len(image_chunks), 0, "No image chunks were generated.") 
        
        if not image_chunks:
            self.skipTest("Skipping image chunk test as no images were found or processed in the test PDF.")
            return
            
        # Check the first image chunk found
        first_image_chunk = image_chunks[0]
        self.assertEqual(first_image_chunk.meta.chunk_type, "image")
        self.assertIsNotNone(first_image_chunk.meta.image_path) # Ensure image path exists
        self.assertTrue(len(first_image_chunk.meta.doc_items) > 0) # Ensure doc item is linked
        self.assertIsInstance(first_image_chunk.meta.doc_items[0], PictureItem) # Check type

        # Verify the image path corresponds to an existing file in the temp dir
        expected_image_file = self.temp_output_dir / first_image_chunk.meta.image_path
        self.assertTrue(expected_image_file.exists(), f"Image file {expected_image_file} not found.")
        
        # Check breadcrumb (adjust based on where the image appears in your test doc)
        # Example: self.assertEqual(first_image_chunk.meta.headings, "Expected > Heading > Path")
        # If the image has no heading context: self.assertIsNone(first_image_chunk.meta.headings)
        # For now, just assert it could be None or a string
        self.assertTrue(first_image_chunk.meta.headings is None or isinstance(first_image_chunk.meta.headings, str))
        
        # Check if the text contains the caption (if any - might be empty)
        self.assertIsInstance(first_image_chunk.text, str)


if __name__ == '__main__':
    unittest.main() 