"""
Test cases for the SQL formatter module.

This module tests the functionality of the SQL formatter, which converts
Docling document data into a standardized JSON format suitable for SQL database ingestion.
"""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test
from src.sql_formatter import SQLFormatter, process_docling_json_to_sql_format


class TestSQLFormatter(unittest.TestCase):
    """Test cases for the SQL formatter functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a sample document data dictionary for testing
        self.sample_document = {
            "metadata": {
                "filename": "test_document.pdf",
                "mimetype": "application/pdf",
                "binary_hash": "abc123"
            },
            "furniture": [
                {"text": "Header Text", "type": "header"},
                {"text": "Footer Text", "type": "footer"},
                {"text": "Page Number", "type": "page_number"}
            ],
            "body": [
                # Text element
                {
                    "type": "text",
                    "text": "This is a sample text paragraph.",
                    "breadcrumb": "Document > Section > Subsection",
                    "prov": {
                        "page_no": 1,
                        "bbox": {"l": 50, "t": 100, "r": 550, "b": 150}
                    },
                    "self_ref": "#/texts/0"
                },
                # Table element
                {
                    "type": "table",
                    "grid": [["Header1", "Header2"], ["Value1", "Value2"]],
                    "caption": "Sample Table",
                    "breadcrumb": "Document > Section > Tables",
                    "prov": {
                        "page_no": 2,
                        "bbox": {"l": 50, "t": 200, "r": 550, "b": 300}
                    },
                    "self_ref": "#/tables/0"
                },
                # Image element
                {
                    "type": "picture",
                    "caption": "Sample Image",
                    "breadcrumb": "Document > Section > Images",
                    "context_before": "Text before the image.",
                    "ocr_text": "Text extracted from image via OCR",
                    "context_after": "Text after the image.",
                    "external_path": "/path/to/images/test_image.png",
                    "mimetype": "image/png",
                    "width": 400,
                    "height": 300,
                    "prov": {
                        "page_no": 3,
                        "bbox": {"l": 100, "t": 150, "r": 500, "b": 450}
                    },
                    "self_ref": "#/pictures/0"
                }
            ]
        }

    def test_process_docling_json_to_sql_format(self):
        """Test the main processing function."""
        # Call the function with sample data
        result = process_docling_json_to_sql_format(self.sample_document, "test-doc-001")
        
        # Verify the overall structure
        self.assertIn("chunks", result)
        self.assertIn("furniture", result)
        self.assertIn("source_metadata", result)
        
        # Verify the source metadata
        self.assertEqual(result["source_metadata"]["filename"], "test_document.pdf")
        self.assertEqual(result["source_metadata"]["mimetype"], "application/pdf")
        self.assertEqual(result["source_metadata"]["binary_hash"], "abc123")
        
        # Verify furniture items
        self.assertEqual(len(result["furniture"]), 3)
        self.assertIn("Header Text", result["furniture"])
        self.assertIn("Footer Text", result["furniture"])
        self.assertIn("Page Number", result["furniture"])
        
        # Verify chunks
        self.assertEqual(len(result["chunks"]), 3)
        
        # Check if all required fields are present in each chunk
        required_fields = [
            "_id", "block_id", "doc_id", "content_type", "file_type", 
            "master_index", "master_index2", "coords_x", "coords_y", 
            "coords_cx", "coords_cy", "author_or_speaker", "added_to_collection", 
            "file_source", "table_block", "modified_date", "created_date", 
            "creator_tool", "external_files", "text_block", "header_text", 
            "text_search", "user_tags", "special_field1", "special_field2", 
            "special_field3", "graph_status", "dialog", "embedding_flags", "metadata"
        ]
        
        for chunk in result["chunks"]:
            for field in required_fields:
                self.assertIn(field, chunk)
    
    def test_text_chunk_processing(self):
        """Test processing of text chunks."""
        result = process_docling_json_to_sql_format(self.sample_document)
        
        # Get the first chunk (text chunk)
        text_chunk = result["chunks"][0]
        
        # Verify content type
        self.assertEqual(text_chunk["content_type"], "text")
        
        # Verify text content
        self.assertIn("This is a sample text paragraph.", text_chunk["text_block"])
        
        # Verify breadcrumb
        self.assertEqual(text_chunk["header_text"], "Document > Section > Subsection")
        
        # Verify coordinates
        self.assertEqual(text_chunk["coords_x"], 50)
        self.assertEqual(text_chunk["coords_y"], 100)
        self.assertEqual(text_chunk["coords_cx"], 500)  # 550 - 50
        self.assertEqual(text_chunk["coords_cy"], 50)   # 150 - 100
        
        # Verify metadata
        self.assertEqual(text_chunk["metadata"]["page_no"], 1)
        self.assertEqual(text_chunk["metadata"]["docling_label"], "text")
    
    def test_table_chunk_processing(self):
        """Test processing of table chunks."""
        result = process_docling_json_to_sql_format(self.sample_document)
        
        # Get the second chunk (table chunk)
        table_chunk = result["chunks"][1]
        
        # Verify content type
        self.assertEqual(table_chunk["content_type"], "table")
        
        # Verify table content
        self.assertIsNotNone(table_chunk["table_block"])
        
        # Parse table_block and verify content
        table_data = json.loads(table_chunk["table_block"])
        self.assertEqual(table_data, [["Header1", "Header2"], ["Value1", "Value2"]])
        
        # Verify text block contains caption
        self.assertIn("Sample Table", table_chunk["text_block"])
        
        # Verify metadata
        self.assertEqual(table_chunk["metadata"]["page_no"], 2)
        self.assertEqual(table_chunk["metadata"]["caption"], "Sample Table")
    
    def test_image_chunk_processing(self):
        """Test processing of image chunks."""
        result = process_docling_json_to_sql_format(self.sample_document)
        
        # Get the third chunk (image chunk)
        image_chunk = result["chunks"][2]
        
        # Verify content type
        self.assertEqual(image_chunk["content_type"], "image")
        
        # Verify external file path
        self.assertEqual(image_chunk["external_files"], "/path/to/images/test_image.png")
        
        # Verify text block contains OCR text
        self.assertIn("[Image Text: Text extracted from image via OCR]", image_chunk["text_block"])
        self.assertIn("Text before the image.", image_chunk["text_block"])
        self.assertIn("Text after the image.", image_chunk["text_block"])
        
        # Verify metadata
        self.assertEqual(image_chunk["metadata"]["page_no"], 3)
        self.assertEqual(image_chunk["metadata"]["caption"], "Sample Image")
        self.assertEqual(image_chunk["metadata"]["image_width"], 400)
        self.assertEqual(image_chunk["metadata"]["image_height"], 300)
        self.assertEqual(image_chunk["metadata"]["image_mimetype"], "image/png")
        self.assertEqual(image_chunk["metadata"]["image_ocr_text"], "Text extracted from image via OCR")
    
    def test_doc_id_assignment(self):
        """Test document ID assignment."""
        # Test with doc_id provided
        result_with_id = process_docling_json_to_sql_format(self.sample_document, "test-doc-123")
        for chunk in result_with_id["chunks"]:
            self.assertEqual(chunk["doc_id"], "test-doc-123")
        
        # Test without doc_id
        result_without_id = process_docling_json_to_sql_format(self.sample_document)
        for chunk in result_without_id["chunks"]:
            self.assertIsNone(chunk["doc_id"])
    
    def test_init_with_defaults(self):
        """Test SQLFormatter initialization with default values."""
        formatter = SQLFormatter()
        
        self.assertEqual(formatter.dialect, 'postgresql')
        self.assertEqual(formatter.table_prefix, '')
        self.assertEqual(formatter.document_table, 'documents')
        self.assertEqual(formatter.content_table, 'document_content')
        
    def test_init_with_custom_values(self):
        """Test SQLFormatter initialization with custom values."""
        formatter = SQLFormatter(
            dialect='mysql',
            table_prefix='test_',
            document_table='my_docs',
            content_table='my_content'
        )
        
        self.assertEqual(formatter.dialect, 'mysql')
        self.assertEqual(formatter.table_prefix, 'test_')
        self.assertEqual(formatter.document_table, 'my_docs')
        self.assertEqual(formatter.content_table, 'my_content')
    
    def test_format_as_sql_basic(self):
        """Test format_as_sql method with basic document."""
        formatter = SQLFormatter()
        result = formatter.format_as_sql(self.sample_document)
        
        # Check basic structure
        self.assertIn('chunks', result)
        self.assertIn('furniture', result)
        self.assertIn('source', result)
        
        # Check source details
        self.assertEqual(result['source']['title'], "Test Document")
        self.assertEqual(result['source']['author'], "Test Author")
        
        # Check chunks are generated for each content item
        self.assertEqual(len(result['chunks']), len(self.sample_document['body']))
    
    def test_format_as_sql_with_standardized_format(self):
        """Test format_as_sql with standardized format flag."""
        formatter = SQLFormatter()
        result = formatter.format_as_sql(self.sample_document, standardized_format=True)
        
        # Ensure standardized fields are preserved
        if len(result['chunks']) > 0:
            self.assertIn('master_index', result['chunks'][0])
            self.assertIn('file_type', result['chunks'][0])
            self.assertIn('page_num', result['chunks'][0])
    
    def test_generate_sql_inserts_postgresql(self):
        """Test generate_sql_inserts with PostgreSQL dialect."""
        formatter = SQLFormatter(dialect='postgresql')
        sql_data = formatter.format_as_sql(self.sample_document)
        inserts = formatter.generate_sql_inserts(sql_data)
        
        # Check PostgreSQL syntax (double quotes for identifiers)
        self.assertIn('INSERT INTO "documents"', inserts)
        self.assertIn('INSERT INTO "document_content"', inserts)
    
    def test_generate_sql_inserts_mysql(self):
        """Test generate_sql_inserts with MySQL dialect."""
        formatter = SQLFormatter(dialect='mysql')
        sql_data = formatter.format_as_sql(self.sample_document)
        inserts = formatter.generate_sql_inserts(sql_data)
        
        # Check MySQL syntax (backticks for identifiers)
        self.assertIn('INSERT INTO `documents`', inserts)
        self.assertIn('INSERT INTO `document_content`', inserts)
    
    def test_generate_sql_inserts_sqlite(self):
        """Test generate_sql_inserts with SQLite dialect."""
        formatter = SQLFormatter(dialect='sqlite')
        sql_data = formatter.format_as_sql(self.sample_document)
        inserts = formatter.generate_sql_inserts(sql_data)
        
        # Check SQLite syntax (no quotes for identifiers)
        self.assertIn('INSERT INTO documents', inserts)
        self.assertIn('INSERT INTO document_content', inserts)
    
    def test_sql_escape_quotes(self):
        """Test SQL escaping of quotes in text."""
        # Data with quotes
        data_with_quotes = {
            "metadata": {"title": "Test \"Quoted\" Title"},
            "content": [
                {
                    "block_id": "block_001",
                    "content_type": "paragraph",
                    "text": "Text with 'single' and \"double\" quotes."
                }
            ]
        }
        
        formatter = SQLFormatter()
        sql_data = formatter.format_as_sql(data_with_quotes)
        inserts = formatter.generate_sql_inserts(sql_data)
        
        # Check that quotes are properly escaped
        self.assertIn("Test \\\"Quoted\\\" Title", inserts)
        self.assertIn("Text with \\'single\\' and \\\"double\\\" quotes", inserts)
    
    def test_save_formatted_output(self):
        """Test saving formatted output to a file."""
        formatter = SQLFormatter()
        sql_data = formatter.format_as_sql(self.sample_document)
        
        # Create a temporary file path
        temp_file = os.path.join(os.path.dirname(__file__), 'temp_sql_output.json')
        
        try:
            # Save the output
            formatter.save_formatted_output(sql_data, temp_file)
            
            # Check the file exists
            self.assertTrue(os.path.exists(temp_file))
            
            # Load the saved data and verify it matches
            with open(temp_file, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data['source']['title'], sql_data['source']['title'])
            self.assertEqual(len(saved_data['chunks']), len(sql_data['chunks']))
            
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)


class TestProcessDoclingJsonToSQL(unittest.TestCase):
    """Unit tests for process_docling_json_to_sql_format function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample document data
        self.sample_data = {
            "metadata": {
                "title": "Test Document",
                "author": "Test Author",
                "source_path": "/path/to/test.pdf",
                "creation_date": "2023-01-01"
            },
            "content": [
                {
                    "block_id": "block_001",
                    "content_type": "heading",
                    "text": "Sample Heading",
                    "level": 1
                },
                {
                    "block_id": "block_002",
                    "content_type": "paragraph",
                    "text": "This is sample paragraph text."
                }
            ]
        }
    
    def test_process_basic_document(self):
        """Test processing a basic document to SQL format."""
        result = process_docling_json_to_sql_format(self.sample_data)
        
        # Check basic structure
        self.assertIn('chunks', result)
        self.assertIn('furniture', result)
        self.assertIn('source', result)
        
        # Check source metadata
        self.assertEqual(result['source']['title'], "Test Document")
        self.assertEqual(result['source']['author'], "Test Author")
        
        # Check content chunks
        self.assertEqual(len(result['chunks']), 2)
        
        # Check first chunk (heading)
        heading_chunk = result['chunks'][0]
        self.assertEqual(heading_chunk['content_type'], 'heading')
        self.assertEqual(heading_chunk['text'], 'Sample Heading')
        self.assertEqual(heading_chunk['block_id'], 'block_001')
        
        # Check second chunk (paragraph)
        paragraph_chunk = result['chunks'][1]
        self.assertEqual(paragraph_chunk['content_type'], 'paragraph')
        self.assertEqual(paragraph_chunk['text'], 'This is sample paragraph text.')
        self.assertEqual(paragraph_chunk['block_id'], 'block_002')
    
    def test_process_with_empty_document(self):
        """Test processing an empty document."""
        empty_data = {
            "metadata": {},
            "content": []
        }
        
        result = process_docling_json_to_sql_format(empty_data)
        
        # Check structure is still valid
        self.assertIn('chunks', result)
        self.assertIn('furniture', result)
        self.assertIn('source', result)
        
        # Check chunks is empty
        self.assertEqual(len(result['chunks']), 0)
    
    def test_process_with_mixed_content(self):
        """Test processing a document with mixed content types."""
        mixed_data = {
            "metadata": {"title": "Mixed Content"},
            "content": [
                {
                    "block_id": "block_001",
                    "content_type": "heading",
                    "text": "Heading",
                    "level": 1
                },
                {
                    "block_id": "block_002",
                    "content_type": "paragraph",
                    "text": "Paragraph text."
                },
                {
                    "block_id": "block_003",
                    "content_type": "list",
                    "items": ["Item 1", "Item 2"]
                },
                {
                    "block_id": "block_004",
                    "content_type": "table",
                    "rows": [["H1", "H2"], ["C1", "C2"]]
                }
            ]
        }
        
        result = process_docling_json_to_sql_format(mixed_data)
        
        # Check all content types are processed
        self.assertEqual(len(result['chunks']), 4)
        
        # Check content types
        content_types = [chunk['content_type'] for chunk in result['chunks']]
        self.assertIn('heading', content_types)
        self.assertIn('paragraph', content_types)
        self.assertIn('list', content_types)
        self.assertIn('table', content_types)
    
    def test_process_with_standardized_format(self):
        """Test processing with standardized format enabled."""
        # Standardized data includes specific fields
        standardized_data = {
            "metadata": self.sample_data["metadata"],
            "content": [
                {
                    "block_id": "block_001",
                    "content_type": "heading",
                    "text": "Sample Heading",
                    "level": 1,
                    "master_index": 0,
                    "file_type": "pdf",
                    "page_num": 1
                }
            ]
        }
        
        result = process_docling_json_to_sql_format(standardized_data, standardized_format=True)
        
        # Check standardized fields are preserved
        self.assertEqual(len(result['chunks']), 1)
        chunk = result['chunks'][0]
        self.assertIn('master_index', chunk)
        self.assertEqual(chunk['master_index'], 0)
        self.assertIn('file_type', chunk)
        self.assertEqual(chunk['file_type'], 'pdf')
        self.assertIn('page_num', chunk)
        self.assertEqual(chunk['page_num'], 1)
    
    @patch('src.sql_formatter.logger')
    def test_process_with_invalid_input(self, mock_logger):
        """Test processing with invalid input data."""
        # None input
        result_none = process_docling_json_to_sql_format(None)
        self.assertIn('chunks', result_none)
        self.assertEqual(len(result_none['chunks']), 0)
        mock_logger.error.assert_called()
        
        # Reset mock
        mock_logger.reset_mock()
        
        # Invalid structure (missing content)
        invalid_data = {"metadata": {}}
        result_invalid = process_docling_json_to_sql_format(invalid_data)
        self.assertIn('chunks', result_invalid)
        self.assertEqual(len(result_invalid['chunks']), 0)
        mock_logger.error.assert_called()


if __name__ == "__main__":
    unittest.main() 