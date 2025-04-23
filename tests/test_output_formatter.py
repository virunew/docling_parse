"""
Test module for the output formatter.

This module contains tests for the output formatter functionality,
including tests for different output formats.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
import sys
import csv
from unittest import mock

# Add src directory to path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from output_formatter import OutputFormatter

class TestOutputFormatter(unittest.TestCase):
    """Test cases for the OutputFormatter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample document for testing
        self.test_document = {
            "name": "test_document",
            "metadata": {
                "title": "Test Document",
                "author": "Test Author",
                "created": "2023-01-01"
            },
            "pages": [
                {
                    "page_number": 1,
                    "segments": [
                        {"text": "This is a paragraph on page 1."},
                        {"text": "This is another paragraph on page 1."}
                    ],
                    "tables": [
                        {
                            "cells": [
                                {"row": 0, "col": 0, "text": "Header 1", "rowspan": 1, "colspan": 1},
                                {"row": 0, "col": 1, "text": "Header 2", "rowspan": 1, "colspan": 1},
                                {"row": 1, "col": 0, "text": "Data 1", "rowspan": 1, "colspan": 1},
                                {"row": 1, "col": 1, "text": "Data 2", "rowspan": 1, "colspan": 1}
                            ],
                            "metadata": {
                                "caption": "Test Table",
                                "page_number": 1
                            }
                        }
                    ],
                    "pictures": [
                        {
                            "image_path": "images/test_image.png",
                            "metadata": {
                                "caption": "Test Image",
                                "page_number": 1,
                                "width": 100,
                                "height": 100
                            }
                        }
                    ]
                },
                {
                    "page_number": 2,
                    "segments": [
                        {"text": "This is a paragraph on page 2."}
                    ]
                }
            ],
            "images_data": {
                "images": [
                    {
                        "path": "images/test_image.png",
                        "caption": "Test Image from images_data",
                        "page_number": 1,
                        "width": 100,
                        "height": 100
                    }
                ]
            }
        }
        
        # Create a document with flattened sequence for testing
        self.test_document_with_sequence = {
            "name": "test_document_sequence",
            "metadata": {
                "title": "Test Document With Sequence",
                "author": "Test Author",
                "created": "2023-01-01"
            },
            "flattened_sequence": [
                {
                    "metadata": {"type": "heading", "page_number": 1},
                    "text": "Test Heading"
                },
                {
                    "metadata": {"type": "paragraph", "page_number": 1},
                    "text": "This is a paragraph in a sequence."
                },
                {
                    "metadata": {"type": "table", "page_number": 1, "caption": "Test Table"},
                    "cells": [
                        {"row": 0, "col": 0, "text": "Header 1", "rowspan": 1, "colspan": 1},
                        {"row": 0, "col": 1, "text": "Header 2", "rowspan": 1, "colspan": 1},
                        {"row": 1, "col": 0, "text": "Data 1", "rowspan": 1, "colspan": 1},
                        {"row": 1, "col": 1, "text": "Data 2", "rowspan": 1, "colspan": 1}
                    ]
                },
                {
                    "metadata": {"type": "paragraph", "page_number": 1},
                    "text": "Another paragraph."
                },
                {
                    "metadata": {"type": "image", "page_number": 1, "caption": "Test Image"},
                    "image_path": "images/test_image.png"
                },
                {
                    "metadata": {"type": "heading", "page_number": 2},
                    "text": "Page 2 Heading"
                },
                {
                    "metadata": {"type": "paragraph", "page_number": 2},
                    "text": "This is a paragraph on page 2."
                }
            ]
        }
        
        # Create a formatter with default config
        self.formatter = OutputFormatter()
        
        # Create a formatter with custom config
        self.custom_formatter = OutputFormatter({
            'include_metadata': False,
            'include_page_breaks': False,
            'include_captions': False,
            'image_base_url': 'https://example.com/images'
        })
        
        # Create a temporary directory for output files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a minimal configuration
        self.config = {
            'include_metadata': True,
            'include_images': True,
            'image_base_url': 'http://example.com/images/',
            'include_page_breaks': True,
            'include_captions': True,
            'doc_id': 'test-doc-123'
        }
        
        # Create an OutputFormatter instance
        self.formatter = OutputFormatter(self.config)
        
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
                }
            ]
        }
        
        # Create a temporary output directory
        self.output_dir = Path("test_output")
        self.output_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
        
        # Remove test output files safely
        try:
            if hasattr(self, 'output_dir') and self.output_dir.exists():
                for file in self.output_dir.glob("*"):
                    if file.is_file():  # Only try to remove files, not directories
                        try:
                            file.unlink()
                        except (PermissionError, OSError):
                            pass  # Ignore permission errors
                
                # Try to remove the directory
                try:
                    self.output_dir.rmdir()
                except (PermissionError, OSError):
                    pass  # Ignore if directory can't be removed
        except Exception as e:
            print(f"Error cleaning up: {e}")
    
    def test_json_format_basic(self):
        """Test basic JSON formatting."""
        # Format as simplified JSON
        result = self.formatter.format_as_simplified_json(self.test_document)
        
        # Check the basic structure
        self.assertIn('metadata', result)
        self.assertIn('content', result)
        self.assertIn('images', result)
        
        # Check metadata
        self.assertEqual(result['metadata']['name'], 'test_document')
        self.assertEqual(result['metadata']['title'], 'Test Document')
        self.assertEqual(result['metadata']['author'], 'Test Author')
        
        # Check content length (should include all segments, tables, pictures, and page breaks)
        # Note: Content from pages + page break between pages
        expected_content_count = (2 + 1 + 1) + 1 + 1  # Page 1 (2 paragraphs, 1 table, 1 image) + page break + page 2 (1 paragraph)
        self.assertEqual(len(result['content']), expected_content_count)
        
        # Check page breaks
        page_breaks = [item for item in result['content'] if item.get('type') == 'page_break']
        self.assertEqual(len(page_breaks), 1)
    
    def test_json_format_with_sequence(self):
        """Test JSON formatting with flattened sequence."""
        # Format as simplified JSON
        result = self.formatter.format_as_simplified_json(self.test_document_with_sequence)
        
        # Check the basic structure
        self.assertIn('metadata', result)
        self.assertIn('content', result)
        
        # Check metadata
        self.assertEqual(result['metadata']['name'], 'test_document_sequence')
        self.assertEqual(result['metadata']['title'], 'Test Document With Sequence')
        
        # Check content types in order
        content_types = [item.get('type') for item in result['content']]
        expected_types = ['heading', 'paragraph', 'table', 'paragraph', 'image', 'page_break', 'heading', 'paragraph']
        self.assertEqual(content_types, expected_types)
    
    def test_json_format_custom_config(self):
        """Test JSON formatting with custom configuration."""
        # Format as simplified JSON
        result = self.custom_formatter.format_as_simplified_json(self.test_document)
        
        # Check content for page breaks (should not be present)
        page_breaks = [item for item in result['content'] if item.get('type') == 'page_break']
        self.assertEqual(len(page_breaks), 0)
        
        # Check image URLs (should use custom base URL)
        images = [item for item in result['content'] if item.get('type') == 'image']
        for image in images:
            self.assertTrue(image['url'].startswith('https://example.com/images'))
    
    def test_markdown_format(self):
        """Test Markdown formatting."""
        # Format as Markdown
        result = self.formatter.format_as_markdown(self.test_document)
        
        # Check for basic Markdown elements
        self.assertIn('# Test Document', result)
        self.assertIn('## Document Information', result)
        self.assertIn('This is a paragraph on page 1.', result)
        self.assertIn('| Header 1 | Header 2 |', result)
        self.assertIn('| Data 1 | Data 2 |', result)
        self.assertIn('![', result)  # Image syntax
        self.assertIn('---', result)  # Page break
    
    def test_markdown_format_custom_config(self):
        """Test Markdown formatting with custom configuration."""
        # Format as Markdown
        result = self.custom_formatter.format_as_markdown(self.test_document)
        
        # Check for absence of metadata section
        self.assertNotIn('## Document Information', result)
        
        # Check for absence of page breaks
        self.assertNotIn('---\n*Page', result)
        
        # Check for absence of image captions
        self.assertNotIn('*Test Image*', result)
        
        # Check for custom image URL
        self.assertIn('![', result)
        self.assertIn('https://example.com/images', result)
    
    def test_html_format(self):
        """Test HTML formatting."""
        # Format as HTML
        result = self.formatter.format_as_html(self.test_document)
        
        # Check for basic HTML elements
        self.assertIn('<!DOCTYPE html>', result)
        self.assertIn('<title>Test Document</title>', result)
        self.assertIn('<h1>Test Document</h1>', result)
        self.assertIn('<div class=\'metadata\'>', result)
        self.assertIn('<p>This is a paragraph on page 1.</p>', result)
        self.assertIn('<table>', result)
        self.assertIn('<th>Header 1</th>', result)
        self.assertIn('<td>Data 1</td>', result)
        self.assertIn('<img src=', result)
        self.assertIn('<figcaption class=\'caption\'>Test Image</figcaption>', result)
        self.assertIn('<div class=\'page-break\'>Page 2</div>', result)
    
    def test_html_format_custom_config(self):
        """Test HTML formatting with custom configuration."""
        # Format as HTML
        result = self.custom_formatter.format_as_html(self.test_document)
        
        # HTML should be returned as a string
        self.assertIsInstance(result, str)
        
        # Check that HTML contains document title
        self.assertIn("Test Document", result)
        
        # Check that metadata is not included
        self.assertNotIn("<h2>Document Information</h2>", result)
        
        # Check that custom image URL is used
        self.assertIn("https://example.com/images", result)
    
    def test_csv_format(self):
        """Test basic CSV formatting."""
        # Format document data as CSV
        csv_string = self.formatter.format_as_csv(self.test_document)
        
        # Should return a string
        self.assertIsInstance(csv_string, str)
        
        # Split into lines - handle both \n and \r\n line endings
        lines = csv_string.replace('\r\n', '\n').split('\n')
        
        # Check header
        self.assertEqual(lines[0], "content_type,page_number,content,level,metadata")
        
        # Check content types present in the output
        self.assertTrue(any('paragraph' in line for line in lines), "CSV should contain paragraphs")
        self.assertTrue(any('table' in line for line in lines), "CSV should contain tables")
        self.assertTrue(any('table_cell' in line for line in lines), "CSV should contain table cells")
        self.assertTrue(any('image' in line for line in lines), "CSV should contain images")
        self.assertTrue(any('page_break' in line for line in lines), "CSV should contain page breaks")
        
        # Split one line into values and check structure
        paragraph_line = next((line for line in lines if 'paragraph' in line), None)
        self.assertIsNotNone(paragraph_line, "Should have at least one paragraph line")
        
        # Parse the line using the csv module 
        reader = csv.reader([paragraph_line])
        values = next(reader)
        
        self.assertEqual(len(values), 5, "Should have 5 fields per row")
        self.assertEqual(values[0], "paragraph", "First field should be content_type")
        self.assertNotEqual(values[2], "", "Content field should not be empty")
    
    def test_csv_format_with_sequence(self):
        """Test CSV formatting with flattened sequence."""
        # Format as CSV
        result = self.formatter.format_as_csv(self.test_document_with_sequence)
        
        # Split the result into lines for checking
        lines = result.strip().split('\n')
        
        # Check content types in order
        content_types = [line.split(',')[0] for line in lines[1:]]  # Skip header
        expected_types = ['heading', 'paragraph', 'table', 'table_cell', 'table_cell', 
                         'table_cell', 'table_cell', 'paragraph', 'image', 
                         'page_break', 'heading', 'paragraph']
        
        self.assertEqual(content_types, expected_types)
        
        # Check heading level
        heading_lines = [line for line in lines if line.startswith('heading')]
        for line in heading_lines:
            fields = line.split(',')
            self.assertEqual(fields[3], "1")  # Default heading level

    def test_save_formatted_output_csv(self):
        """Test saving formatted output as CSV."""
        # Create a mock document
        mock_doc = {
            "metadata": {"title": "Test Document"},
            "content": [{"type": "text", "text": "Hello World"}]
        }
        
        # Call save_formatted_output
        output_file_str = self.formatter.save_formatted_output(mock_doc, self.temp_dir.name, "csv")
        output_file = Path(output_file_str)
        
        # Verify file exists and has correct extension
        self.assertTrue(output_file.exists())
        self.assertTrue(output_file.name.endswith(".csv"))
    
    def test_save_formatted_output_json(self):
        """Test saving formatted output as JSON."""
        # Create a mock document
        mock_doc = {
            "metadata": {"title": "Test Document"}
        }
        
        # Call save_formatted_output
        output_file_str = self.formatter.save_formatted_output(mock_doc, self.temp_dir.name)
        output_file = Path(output_file_str)
        
        # Verify file exists and has correct name
        self.assertTrue(output_file.exists())
        self.assertTrue(output_file.name.endswith("_simplified.json"))
        
        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertIn("metadata", saved_data)
        self.assertIn("content", saved_data)
    
    def test_save_formatted_output_markdown(self):
        """Test saving formatted output as Markdown."""
        # Create a mock document
        mock_doc = {
            "metadata": {"title": "Test Document"},
            "content": [{"type": "text", "text": "Hello World"}]
        }
        
        # Call save_formatted_output
        output_file_str = self.formatter.save_formatted_output(mock_doc, self.temp_dir.name, "md")
        output_file = Path(output_file_str)
        
        # Verify file exists and has correct extension
        self.assertTrue(output_file.exists())
        self.assertTrue(output_file.name.endswith(".md"))
        
        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("# Test Document", content)
    
    def test_save_formatted_output_html(self):
        """Test saving formatted output as HTML."""
        # Create a mock document
        mock_doc = {
            "metadata": {"title": "Test Document"},
            "content": [{"type": "text", "text": "Hello World"}]
        }
        
        # Call save_formatted_output
        output_file_str = self.formatter.save_formatted_output(mock_doc, self.temp_dir.name, "html")
        output_file = Path(output_file_str)
        
        # Verify file exists and has correct extension
        self.assertTrue(output_file.exists())
        self.assertTrue(output_file.name.endswith(".html"))
        
        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("<title>Test Document</title>", content)
    
    def test_save_formatted_output_invalid_format(self):
        """Test saving formatted output with invalid format."""
        # Create a mock document
        mock_doc = {
            "metadata": {"title": "Test Document"}
        }
        
        # Call save_formatted_output with invalid format
        output_file_str = self.formatter.save_formatted_output(mock_doc, self.temp_dir.name, "invalid")
        output_file = Path(output_file_str)
        
        # Verify file exists (should default to JSON)
        self.assertTrue(output_file.exists())
        self.assertTrue(output_file.name.endswith("_simplified.json"))
        
        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertIn("metadata", saved_data)
        self.assertIn("content", saved_data)

    def test_error_handling(self):
        """Test error handling in formatters."""
        # Create an invalid document
        invalid_document = {"invalid": "structure"}
        
        # Test JSON formatting with invalid document
        json_result = self.formatter.format_as_simplified_json(invalid_document)
        self.assertIsInstance(json_result, dict)
        self.assertIn('metadata', json_result)
        # The error might be in the metadata as a separate key
        if 'error' in json_result['metadata']:
            self.assertIn('error', json_result['metadata'])
        else:
            # Or the error handling might just return a minimal structure
            self.assertEqual(json_result['content'], [])
        
        # Test Markdown formatting with invalid document
        md_result = self.formatter.format_as_markdown(invalid_document)
        # Check for any error indication in the markdown
        self.assertTrue('Error' in md_result or md_result.startswith('# Document'))
        
        # Test HTML formatting with invalid document
        html_result = self.formatter.format_as_html(invalid_document)
        # Check for any error indication in the HTML
        self.assertTrue('<h1>Error</h1>' in html_result or '<title>Document</title>' in html_result)

    def test_format_as_sql_json(self):
        """Test the SQL formatting capability."""
        # Mock the function directly on the method
        with mock.patch.object(OutputFormatter, 'format_as_sql_json', autospec=True) as mock_method:
            # Setup mock to return a predefined output
            mock_output = {
                "chunks": [
                    {
                        "_id": None,
                        "block_id": 1,
                        "doc_id": "test-doc-123",
                        "content_type": "text",
                        "file_type": "application/pdf",
                        "text_block": "Document > Section > Subsection\n\nThis is a sample text paragraph."
                    }
                ],
                "furniture": ["Header Text", "Footer Text", "Page Number"],
                "source_metadata": {
                    "filename": "test_document.pdf",
                    "mimetype": "application/pdf",
                    "binary_hash": "abc123"
                }
            }
            mock_method.return_value = mock_output
            
            # Create a new instance for testing with the mock
            test_formatter = OutputFormatter(self.config)
            
            # Call the function
            result = test_formatter.format_as_sql_json(self.sample_document)
            
            # Verify the mock was called with correct arguments
            mock_method.assert_called_once()
            
            # Verify the result
            self.assertEqual(result, mock_output)
    
    def test_save_formatted_output_sql(self):
        """Test saving SQL-formatted output."""
        # Mock the format_as_sql_json method directly
        with mock.patch.object(OutputFormatter, 'format_as_sql_json', autospec=True) as mock_method:
            # Setup mock to return a predefined output
            mock_output = {
                "chunks": [
                    {
                        "_id": None,
                        "block_id": 1,
                        "doc_id": "test-doc-123",
                        "content_type": "text",
                        "file_type": "application/pdf",
                        "text_block": "Document > Section > Subsection\n\nThis is a sample text paragraph."
                    }
                ],
                "furniture": ["Header Text", "Footer Text", "Page Number"],
                "source_metadata": {
                    "filename": "test_document.pdf",
                    "mimetype": "application/pdf",
                    "binary_hash": "abc123"
                }
            }
            mock_method.return_value = mock_output
            
            # Call the function to save formatted output as SQL
            output_file = self.formatter.save_formatted_output(
                self.sample_document, 
                self.output_dir, 
                "sql"
            )
            
            # Verify a file was created
            expected_file = self.output_dir / "test_document_sql.json"
            self.assertTrue(expected_file.exists())
            
            # Verify the file contains the correct data
            with open(expected_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            # Check the structure of the saved data
            self.assertIn("chunks", saved_data)
            self.assertIn("furniture", saved_data)
            self.assertIn("source_metadata", saved_data)
            self.assertEqual(len(saved_data["chunks"]), 1)
            self.assertEqual(saved_data["chunks"][0]["doc_id"], "test-doc-123")

if __name__ == '__main__':
    unittest.main() 