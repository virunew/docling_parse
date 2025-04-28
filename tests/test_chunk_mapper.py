import json
import os
import sys
import unittest
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.chunk_mapper import ChunkMapper, map_chunks_to_spec

class TestChunkMapper(unittest.TestCase):
    """Tests for the ChunkMapper class and related functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample chunk data
        self.text_chunk = {
            "breadcrumb": "Document > Section 1",
            "content": "This is a sample text paragraph.",
            "element_type": "text",
            "page_no": 1,
            "bbox": {"l": 50, "t": 100, "r": 550, "b": 150},
            "self_ref": "#/texts/0",
            "source": "test_document.pdf"
        }
        
        self.image_chunk = {
            "breadcrumb": "Document > Section 2",
            "element_type": "picture",
            "image_path": "images/test_image.png",
            "page_no": 2,
            "bbox": {"l": 100, "t": 200, "r": 500, "b": 400},
            "self_ref": "#/pictures/0",
            "ocr_text": "Text extracted from image",
            "context_before": "Text before the image.",
            "context_after": "Text after the image.",
            "caption": "Image Caption",
            "source": "test_document.pdf",
            "mimetype": "image/png",
            "width": 400,
            "height": 200
        }
        
        self.table_chunk = {
            "breadcrumb": "Document > Section 3",
            "element_type": "table",
            "table_data": [["Cell 1", "Cell 2"], ["Cell 3", "Cell 4"]],
            "page_no": 3,
            "bbox": {"l": 50, "t": 300, "r": 550, "b": 400},
            "self_ref": "#/tables/0",
            "source": "test_document.pdf"
        }
        
        self.sample_chunks = [
            self.text_chunk,
            self.image_chunk,
            self.table_chunk
        ]
        
        # Create a test output directory
        self.test_output_dir = Path("test_output")
        self.test_output_dir.mkdir(exist_ok=True)
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test output files
        for file in self.test_output_dir.glob("*"):
            file.unlink()
        
        # Remove test output directory
        self.test_output_dir.rmdir()
    
    def test_chunk_mapper_initialization(self):
        """Test that ChunkMapper initializes correctly."""
        mapper = ChunkMapper()
        self.assertEqual(mapper.creator_tool, "DoclingToJsonScript_V1.1")
        
        custom_tool = "CustomTool_v1.0"
        mapper = ChunkMapper(creator_tool=custom_tool)
        self.assertEqual(mapper.creator_tool, custom_tool)
    
    def test_determine_content_type(self):
        """Test content type determination from chunk data."""
        mapper = ChunkMapper()
        
        self.assertEqual(mapper._determine_content_type(self.text_chunk), "text")
        self.assertEqual(mapper._determine_content_type(self.image_chunk), "image")
        self.assertEqual(mapper._determine_content_type(self.table_chunk), "table")
        
        # Test with empty chunk
        self.assertEqual(mapper._determine_content_type({}), "text")
    
    def test_get_coordinates(self):
        """Test coordinate extraction from bbox data."""
        mapper = ChunkMapper()
        
        # Test coordinates for the image chunk
        self.assertEqual(mapper._get_coordinate(self.image_chunk, "x"), 100)
        self.assertEqual(mapper._get_coordinate(self.image_chunk, "y"), 200)
        self.assertEqual(mapper._get_coordinate(self.image_chunk, "width"), 400)
        self.assertEqual(mapper._get_coordinate(self.image_chunk, "height"), 200)
        
        # Test with missing bbox
        no_bbox_chunk = {"element_type": "text"}
        self.assertEqual(mapper._get_coordinate(no_bbox_chunk, "x"), 0)
    
    def test_format_text_block(self):
        """Test text block formatting for different content types."""
        mapper = ChunkMapper()
        
        # Test text chunk
        expected_text = "Document > Section 1\n\nThis is a sample text paragraph."
        self.assertEqual(mapper._format_text_block(self.text_chunk), expected_text)
        
        # Test image chunk
        expected_image_text = "Document > Section 2\n\nText before the image.\n\n[Image Text: Text extracted from image]\n\nText after the image."
        self.assertEqual(mapper._format_text_block(self.image_chunk), expected_image_text)
    
    def test_create_metadata_object(self):
        """Test metadata object creation from chunk data."""
        mapper = ChunkMapper()
        
        # Test metadata for text chunk
        text_metadata = mapper._create_metadata_object(self.text_chunk)
        self.assertEqual(text_metadata["breadcrumb"], "Document > Section 1")
        self.assertEqual(text_metadata["page_no"], 1)
        self.assertEqual(text_metadata["docling_ref"], "#/texts/0")
        
        # Test metadata for image chunk with additional fields
        image_metadata = mapper._create_metadata_object(self.image_chunk)
        self.assertEqual(image_metadata["caption"], "Image Caption")
        self.assertEqual(image_metadata["context_before"], "Text before the image.")
        self.assertEqual(image_metadata["image_mimetype"], "image/png")
        self.assertEqual(image_metadata["image_width"], 400)
    
    def test_map_chunks(self):
        """Test mapping of chunks to the standardized format."""
        mapper = ChunkMapper()
        mapped_chunks = mapper.map_chunks(self.sample_chunks, doc_id="test-123")
        
        # Check we have the right number of chunks
        self.assertEqual(len(mapped_chunks), 3)
        
        # Check basic mapping for first (text) chunk
        text_mapped = mapped_chunks[0]
        self.assertEqual(text_mapped["block_id"], 1)
        self.assertEqual(text_mapped["doc_id"], "test-123")
        self.assertEqual(text_mapped["content_type"], "text")
        self.assertEqual(text_mapped["master_index"], 1)
        self.assertEqual(text_mapped["header_text"], "Document > Section 1")
        self.assertEqual(text_mapped["special_field2"], "Document > Section 1")
        
        # Check image-specific fields
        image_mapped = mapped_chunks[1]
        self.assertEqual(image_mapped["content_type"], "image")
        self.assertEqual(image_mapped["external_files"], "images/test_image.png")
        
        # Check table-specific fields
        table_mapped = mapped_chunks[2]
        self.assertEqual(table_mapped["content_type"], "table")
        self.assertEqual(json.loads(table_mapped["table_block"]), 
                        [["Cell 1", "Cell 2"], ["Cell 3", "Cell 4"]])
    
    def test_map_chunks_with_json_strings(self):
        """Test mapping of chunks that are JSON strings."""
        json_chunks = [json.dumps(chunk) for chunk in self.sample_chunks]
        
        mapper = ChunkMapper()
        mapped_chunks = mapper.map_chunks(json_chunks, doc_id="test-123")
        
        # Check we have the right number of chunks
        self.assertEqual(len(mapped_chunks), 3)
        
        # Check content types are preserved
        self.assertEqual(mapped_chunks[0]["content_type"], "text")
        self.assertEqual(mapped_chunks[1]["content_type"], "image")
        self.assertEqual(mapped_chunks[2]["content_type"], "table")
    
    def test_map_chunks_to_spec_with_list(self):
        """Test the map_chunks_to_spec function with a list of chunks."""
        output_file = self.test_output_dir / "test_output.json"
        
        result = map_chunks_to_spec(self.sample_chunks, str(output_file), doc_id="test-doc")
        
        # Check the result is returned
        self.assertEqual(len(result), 3)
        
        # Check the file was created
        self.assertTrue(output_file.exists())
        
        # Check the file content
        with open(output_file, 'r') as f:
            output_data = json.load(f)
        
        self.assertEqual(len(output_data["chunks"]), 3)
        self.assertEqual(output_data["source_metadata"]["doc_id"], "test-doc")
        self.assertEqual(output_data["source_metadata"]["chunk_count"], 3)

if __name__ == '__main__':
    unittest.main() 