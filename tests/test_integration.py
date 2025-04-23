"""
Integration Tests for PDF Document Parsing

This module contains integration tests to verify that the document parsing 
functionality works correctly from end to end, including image extraction.
"""

import unittest
import os
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import subprocess

# Import docling fix helper
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import docling_fix

# Import test utilities for mock setup
from tests.test_utils import setup_mock_docling, setup_temp_dir, cleanup_temp_dir

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import necessary modules for testing
from src.parse_helper import process_pdf_document, save_output
from src.image_extraction_module import process_pdf_for_images
from src.parse_main import main, Configuration, parse_arguments

# Add src directory to path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the OutputFormatter class for testing formatted output
from src.output_formatter import OutputFormatter

# Import the SQLFormatter class for testing SQL output
from src.sql_formatter import SQLFormatter

class TestDocumentParsingIntegration(unittest.TestCase):
    """Integration tests for the document parsing process."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary output directory
        self.output_dir = Path("tests/temp_output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock PDF path
        self.pdf_path = Path("tests/data/test.pdf")
        
        # Mock document data
        self.mock_document = MagicMock()
        self.mock_document.name = "test_document"
        
        # Create directory for the mocked document
        self.doc_output_dir = self.output_dir / "test_document"
        self.doc_output_dir.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary output directory
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
    
    @patch('src.parse_helper.convert_pdf_document')
    @patch('src.parse_helper.build_element_map')
    @patch('src.parse_helper.process_pdf_for_images')
    def test_process_pdf_document_with_images(self, mock_process_images, mock_build_element_map, mock_convert_pdf):
        """Test processing a PDF document with image extraction."""
        # Configure mocks
        mock_convert_pdf.return_value = self.mock_document
        
        # Mock element map
        mock_element_map = {
            "flattened_sequence": [
                {"id": "elem1", "type": "text", "content": "Test text"},
                {"id": "elem2", "type": "image", "content": ""}
            ],
            "elements": {
                "elem1": {"id": "elem1", "type": "text"},
                "elem2": {"id": "elem2", "type": "image"}
            }
        }
        mock_build_element_map.return_value = mock_element_map
        
        # Mock image processing
        mock_process_images.return_value = {
            "images": [
                {
                    "metadata": {
                        "id": "test_image_1",
                        "format": "image/png",
                        "file_path": f"{self.doc_output_dir}/images/test_image_1.png"
                    }
                }
            ],
            "extraction_stats": {
                "successful": 1,
                "failed": 0,
                "retried": 0,
                "total_time": 0.5
            }
        }
        
        # Call the function
        result = process_pdf_document(self.pdf_path, self.output_dir)
        
        # Verify the results
        self.assertEqual(result, self.mock_document)
        
        # Verify that convert_pdf_document was called correctly
        mock_convert_pdf.assert_called_once()
        
        # Verify that build_element_map was called correctly
        mock_build_element_map.assert_called_once_with(self.mock_document)
        
        # Verify that process_pdf_for_images was called correctly
        mock_process_images.assert_called_once()
    
    @patch('src.parse_helper.convert_pdf_document')
    @patch('src.parse_helper.build_element_map')
    @patch('src.parse_helper.process_pdf_for_images')
    @patch('src.parse_helper.PDFImageExtractor')
    def test_process_pdf_document_with_fallback(self, mock_pdf_extractor_class, mock_process_images, 
                                              mock_build_element_map, mock_convert_pdf):
        """Test processing a PDF document with fallback to legacy image extraction."""
        # Configure mocks
        mock_convert_pdf.return_value = self.mock_document
        
        # Mock element map
        mock_element_map = {
            "flattened_sequence": [
                {"id": "elem1", "type": "text", "content": "Test text"},
                {"id": "elem2", "type": "image", "content": ""}
            ],
            "elements": {
                "elem1": {"id": "elem1", "type": "text"},
                "elem2": {"id": "elem2", "type": "image"}
            }
        }
        mock_build_element_map.return_value = mock_element_map
        
        # Mock process_pdf_for_images to raise an exception
        mock_process_images.side_effect = RuntimeError("Test error")
        
        # Mock legacy extractor
        mock_extractor = mock_pdf_extractor_class.return_value
        mock_extractor.extract_images.return_value = {
            "images": [
                {
                    "raw_data": b"test_image_data",
                    "metadata": {
                        "id": "test_image_1",
                        "format": "image/png"
                    }
                }
            ]
        }
        
        # Call the function
        result = process_pdf_document(self.pdf_path, self.output_dir)
        
        # Verify the results
        self.assertEqual(result, self.mock_document)
        
        # Verify that process_pdf_for_images was called
        mock_process_images.assert_called_once()
        
        # Verify that the fallback extractor was called
        mock_pdf_extractor_class.assert_called_once()
        mock_extractor.extract_images.assert_called_once_with(self.pdf_path)
    
    @patch('src.parse_helper.serialize_docling_document')
    def test_save_output(self, mock_serialize):
        """Test saving output to a file."""
        # Mock serialization result
        mock_serialize.return_value = {
            "name": "test_document",
            "content": "Test content"
        }
        
        # Create a mock images_data.json file
        images_data = {
            "images": [
                {
                    "metadata": {
                        "id": "test_image_1",
                        "format": "image/png"
                    }
                }
            ]
        }
        
        # Create directory structure
        doc_dir = self.output_dir / "test_document"
        doc_dir.mkdir(parents=True, exist_ok=True)
        
        # Write the mock images_data.json file
        with open(doc_dir / "images_data.json", "w") as f:
            json.dump(images_data, f)
        
        # Call the function
        result = save_output(self.mock_document, self.output_dir)
        
        # Verify the results
        expected_path = self.output_dir / "test_document.json"
        self.assertEqual(result, expected_path)
        self.assertTrue(expected_path.exists())
        
        # Verify that the output file contains the merged data
        with open(expected_path, "r") as f:
            data = json.load(f)
        
        self.assertEqual(data["name"], "test_document")
        self.assertEqual(data["content"], "Test content")
        self.assertIn("images_data", data)


class TestIntegration(unittest.TestCase):
    """Integration tests for the PDF parsing and formatting workflow."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are reused across tests."""
        # Check if there's a sample PDF for testing
        cls.sample_pdf_path = None
        
        # First, check in tests/samples
        sample_dir = Path(os.path.dirname(__file__)) / 'samples'
        if sample_dir.exists():
            for pdf_file in sample_dir.glob('*.pdf'):
                cls.sample_pdf_path = pdf_file
                break
        
        # If no sample found, check in project root
        if cls.sample_pdf_path is None:
            project_root = Path(os.path.dirname(__file__)).parent
            for pdf_file in project_root.glob('*.pdf'):
                cls.sample_pdf_path = pdf_file
                break
            
        # Skip tests if no sample found
        if cls.sample_pdf_path is None:
            cls.skip_tests = True
            cls.skip_reason = "No sample PDF file found for testing"
        else:
            cls.skip_tests = False
            cls.skip_reason = None
    
    def setUp(self):
        """Set up test-specific fixtures."""
        # Skip if no sample PDF
        if self.skip_tests:
            self.skipTest(self.skip_reason)
            
        # Create a temporary directory for outputs
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Create a mock document for testing
        self.mock_document, self.mock_processor = setup_mock_docling()
    
    def tearDown(self):
        """Clean up test-specific fixtures."""
        if hasattr(self, 'temp_dir'):
            self.temp_dir.cleanup()
    
    def test_parse_main_json_output(self):
        """Test parsing a PDF and generating JSON output."""
        # Skip if no sample PDF
        if self.skip_tests:
            self.skipTest(self.skip_reason)
            
        # Run the parse_main.py script with JSON output format
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), '../src/parse_main.py'),
            '--pdf_path', str(self.sample_pdf_path),
            '--output_dir', str(self.output_dir),
            '--output_format', 'json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check if the process ran successfully
        self.assertEqual(result.returncode, 0, f"parse_main.py failed with error: {result.stderr}")
        
        # Check if the standard output file exists
        pdf_name = self.sample_pdf_path.stem
        standard_output_file = self.output_dir / f"{pdf_name}.json"
        self.assertTrue(standard_output_file.exists(), f"Standard output file not found: {standard_output_file}")
        
        # Check if the simplified JSON output file exists
        simplified_output_file = self.output_dir / f"{pdf_name}_simplified.json"
        self.assertTrue(simplified_output_file.exists(), f"Simplified JSON output file not found: {simplified_output_file}")
        
        # Verify the simplified JSON output
        try:
            with open(simplified_output_file, 'r', encoding='utf-8') as f:
                simplified_data = json.load(f)
                
            # Check the basic structure
            self.assertIn('metadata', simplified_data, "Missing 'metadata' in simplified output")
            self.assertIn('content', simplified_data, "Missing 'content' in simplified output")
        except json.JSONDecodeError as e:
            self.fail(f"Failed to parse simplified JSON output: {e}")
    
    def test_parse_main_markdown_output(self):
        """Test parsing a PDF and generating Markdown output."""
        # Skip if no sample PDF
        if self.skip_tests:
            self.skipTest(self.skip_reason)
            
        # Run the parse_main.py script with Markdown output format
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), '../src/parse_main.py'),
            '--pdf_path', str(self.sample_pdf_path),
            '--output_dir', str(self.output_dir),
            '--output_format', 'md'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check if the process ran successfully
        self.assertEqual(result.returncode, 0, f"parse_main.py failed with error: {result.stderr}")
        
        # Check if the Markdown output file exists
        pdf_name = self.sample_pdf_path.stem
        markdown_output_file = self.output_dir / f"{pdf_name}.md"
        self.assertTrue(markdown_output_file.exists(), f"Markdown output file not found: {markdown_output_file}")
        
        # Verify the Markdown output
        with open(markdown_output_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
            
        # Check for basic Markdown elements
        self.assertIn('#', markdown_content, "Missing heading in Markdown output")
        self.assertGreater(len(markdown_content), 0, "Markdown output is empty")
    
    def test_parse_main_html_output(self):
        """Test parsing a PDF and generating HTML output."""
        # Skip if no sample PDF
        if self.skip_tests:
            self.skipTest(self.skip_reason)
            
        # Run the parse_main.py script with HTML output format
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), '../src/parse_main.py'),
            '--pdf_path', str(self.sample_pdf_path),
            '--output_dir', str(self.output_dir),
            '--output_format', 'html'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check if the process ran successfully
        self.assertEqual(result.returncode, 0, f"parse_main.py failed with error: {result.stderr}")
        
        # Check if the HTML output file exists
        pdf_name = self.sample_pdf_path.stem
        html_output_file = self.output_dir / f"{pdf_name}.html"
        self.assertTrue(html_output_file.exists(), f"HTML output file not found: {html_output_file}")
        
        # Verify the HTML output
        with open(html_output_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Check for basic HTML elements
        self.assertIn('<!DOCTYPE html>', html_content, "Missing doctype in HTML output")
        self.assertIn('<html>', html_content, "Missing html tag in HTML output")
        self.assertIn('<body>', html_content, "Missing body tag in HTML output")
        self.assertGreater(len(html_content), 0, "HTML output is empty")
    
    def test_parse_main_custom_options(self):
        """Test parsing a PDF with custom formatting options."""
        # Skip if no sample PDF
        if self.skip_tests:
            self.skipTest(self.skip_reason)
            
        # Run the parse_main.py script with custom options
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), '../src/parse_main.py'),
            '--pdf_path', str(self.sample_pdf_path),
            '--output_dir', str(self.output_dir),
            '--output_format', 'json',
            '--no_metadata',
            '--no_page_breaks',
            '--image_base_url', 'https://example.com/images'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check if the process ran successfully
        self.assertEqual(result.returncode, 0, f"parse_main.py failed with error: {result.stderr}")
        
        # Check if the simplified JSON output file exists
        pdf_name = self.sample_pdf_path.stem
        simplified_output_file = self.output_dir / f"{pdf_name}_simplified.json"
        self.assertTrue(simplified_output_file.exists(), f"Simplified JSON output file not found: {simplified_output_file}")
        
        # Verify the simplified JSON output
        try:
            with open(simplified_output_file, 'r', encoding='utf-8') as f:
                simplified_data = json.load(f)
            
            # Check impact of custom options
            # Should still have metadata field but it may be empty or minimal
            self.assertIn('metadata', simplified_data)
            
            # Check content for page breaks (should not be present)
            page_breaks = [item for item in simplified_data.get('content', []) if item.get('type') == 'page_break']
            self.assertEqual(len(page_breaks), 0, "Page breaks should not be present")
            
            # Check image URLs if there are any images
            images = [item for item in simplified_data.get('content', []) if item.get('type') == 'image']
            for image in images:
                if 'url' in image and image['url']:
                    self.assertTrue(image['url'].startswith('https://example.com/images'), 
                                   f"Image URL doesn't use custom base URL: {image['url']}")
        except json.JSONDecodeError as e:
            self.fail(f"Failed to parse simplified JSON output: {e}")
    
    def test_direct_integration_with_formatter(self):
        """Test direct integration between parse_helper output and OutputFormatter."""
        # Skip if no sample PDF
        if self.skip_tests:
            self.skipTest(self.skip_reason)
            
        # Run the parse_main.py script to generate standard JSON output
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), '../src/parse_main.py'),
            '--pdf_path', str(self.sample_pdf_path),
            '--output_dir', str(self.output_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check if the process ran successfully
        self.assertEqual(result.returncode, 0, f"parse_main.py failed with error: {result.stderr}")
        
        # Load the standard output JSON
        pdf_name = self.sample_pdf_path.stem
        standard_output_file = self.output_dir / f"{pdf_name}.json"
        self.assertTrue(standard_output_file.exists())
        
        with open(standard_output_file, 'r', encoding='utf-8') as f:
            document_data = json.load(f)
        
        # Now use the OutputFormatter directly
        formatter = OutputFormatter()
        
        # Test all output formats
        for format_type in ['json', 'md', 'html']:
            # Save formatted output
            output_file = formatter.save_formatted_output(
                document_data,
                self.output_dir,
                format_type
            )
            
            # Check if the file exists
            self.assertTrue(output_file.exists())
            
            # Check file extension matches format
            if format_type == 'json':
                self.assertTrue(output_file.name.endswith('_simplified.json'))
            elif format_type == 'md':
                self.assertTrue(output_file.name.endswith('.md'))
            elif format_type == 'html':
                self.assertTrue(output_file.name.endswith('.html'))
            
            # Check file content is not empty
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertGreater(len(content), 0)

    @patch('src.parse_main.process_pdf_document')
    def test_sql_output_format(self, mock_process):
        """Test that the main function correctly outputs SQL format."""
        # Setup the mock to return our test document
        mock_process.return_value = self.mock_document
        
        # Prepare arguments for SQL output
        test_args = [
            '--input', 'dummy.pdf',
            '--format', 'sql',
            '--output', str(self.output_dir / "output.sql")
        ]
        
        # Run the main function with the test arguments
        with patch('sys.argv', ['parse_main.py'] + test_args):
            main()
        
        # Check that the output file was created
        output_file = self.output_dir / "output.sql"
        self.assertTrue(output_file.exists(), f"Output file {output_file} was not created")
        
        # Read the output file and check it has SQL content
        with open(output_file, 'r') as f:
            sql_content = f.read()
        
        # Verify SQL structure (basic checks)
        self.assertIn("CREATE TABLE", sql_content, "SQL output should contain CREATE TABLE statements")
        self.assertIn("INSERT INTO", sql_content, "SQL output should contain INSERT INTO statements")
        
        # Verify document metadata in SQL
        self.assertIn("Test Document", sql_content, "Document title should be in SQL output")
        self.assertIn("Test Author", sql_content, "Document author should be in SQL output")

    def test_sql_formatter_direct(self):
        """Test SQLFormatter directly to ensure it correctly formats document to SQL."""
        # Create a formatter instance
        formatter = SQLFormatter()
        
        # Format the document
        sql_output = formatter.format(self.mock_document)
        
        # Check the formatted output
        self.assertIsInstance(sql_output, str, "Formatter should return a string")
        self.assertIn("CREATE TABLE", sql_output, "SQL output should contain CREATE TABLE statements")
        self.assertIn("INSERT INTO", sql_output, "SQL output should contain INSERT INTO statements")
        
        # Verify tables for document metadata, pages, segments, and other structures
        self.assertIn("CREATE TABLE document_metadata", sql_output)
        self.assertIn("CREATE TABLE pages", sql_output)
        self.assertIn("CREATE TABLE segments", sql_output)
        
        # Test saving the output to a file
        output_file = self.output_dir / "direct_output.sql"
        formatter.save(sql_output, output_file)
        
        # Verify the file exists and contains the expected content
        self.assertTrue(output_file.exists(), f"Output file {output_file} was not created")
        with open(output_file, 'r') as f:
            saved_content = f.read()
        self.assertEqual(sql_output, saved_content, "Saved content should match formatted output")

    @patch('src.parse_main.process_pdf_document')
    def test_configuration_with_sql_formatter(self, mock_process):
        """Test the integration of Configuration class with SQLFormatter."""
        # Setup the mock to return our test document
        mock_process.return_value = self.mock_document
        
        # Create a configuration
        output_path = self.output_dir / "config_output.sql"
        config = Configuration(
            input_file="dummy.pdf",
            format="sql",
            output_file=str(output_path)
        )
        
        # Run the main function with the configuration
        main(configuration=config)
        
        # Verify the output file exists
        self.assertTrue(output_path.exists(), f"Output file {output_path} was not created")
        
        # Read the output file and check it has SQL content
        with open(output_path, 'r') as f:
            sql_content = f.read()
        
        # Verify SQL content
        self.assertIn("CREATE TABLE", sql_content)
        self.assertIn("INSERT INTO", sql_content)
        self.assertIn("Test Document", sql_content)  # Check document title is included


class TestOutputFormatterIntegration(unittest.TestCase):
    """Integration tests for the OutputFormatter with sample JSON data."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Create a sample document JSON for testing
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
        
        # Save the test document to a JSON file
        self.test_json_path = self.output_dir / "test_document.json"
        with open(self.test_json_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_document, f, indent=2)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_format_as_json(self):
        """Test formatting document as JSON."""
        # Create formatter with default config
        formatter = OutputFormatter()
        
        # Format the document as JSON
        formatted_output_file = formatter.save_formatted_output(
            self.test_document,
            self.output_dir,
            'json'
        )
        
        # Check if file exists
        self.assertTrue(formatted_output_file.exists())
        
        # Check file extension
        self.assertTrue(formatted_output_file.name.endswith('_simplified.json'))
        
        # Check file content
        with open(formatted_output_file, 'r', encoding='utf-8') as f:
            formatted_data = json.load(f)
            
        # Verify structure
        self.assertIn('metadata', formatted_data)
        self.assertIn('content', formatted_data)
        self.assertIn('images', formatted_data)
        
        # Verify content
        self.assertEqual(formatted_data['metadata']['name'], 'test_document')
        self.assertEqual(formatted_data['metadata']['title'], 'Test Document')
        
        # Count content items (should include all segments, tables, pictures, and page breaks)
        expected_content_count = (2 + 1 + 1) + 1 + 1  # Page 1 (2 paragraphs, 1 table, 1 image) + page break + page 2 (1 paragraph)
        self.assertEqual(len(formatted_data['content']), expected_content_count)
    
    def test_format_as_markdown(self):
        """Test formatting document as Markdown."""
        # Create formatter with default config
        formatter = OutputFormatter()
        
        # Format the document as Markdown
        formatted_output_file = formatter.save_formatted_output(
            self.test_document,
            self.output_dir,
            'md'
        )
        
        # Check if file exists
        self.assertTrue(formatted_output_file.exists())
        
        # Check file extension
        self.assertTrue(formatted_output_file.name.endswith('.md'))
        
        # Check file content
        with open(formatted_output_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
            
        # Verify content
        self.assertIn('# Test Document', markdown_content)
        self.assertIn('## Document Information', markdown_content)
        self.assertIn('This is a paragraph on page 1.', markdown_content)
        self.assertIn('| Header 1 | Header 2 |', markdown_content)
        self.assertIn('| Data 1 | Data 2 |', markdown_content)
        self.assertIn('![', markdown_content)  # Image syntax
        self.assertIn('---', markdown_content)  # Page break
    
    def test_format_as_html(self):
        """Test formatting document as HTML."""
        # Create formatter with default config
        formatter = OutputFormatter()
        
        # Format the document as HTML
        formatted_output_file = formatter.save_formatted_output(
            self.test_document,
            self.output_dir,
            'html'
        )
        
        # Check if file exists
        self.assertTrue(formatted_output_file.exists())
        
        # Check file extension
        self.assertTrue(formatted_output_file.name.endswith('.html'))
        
        # Check file content
        with open(formatted_output_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Verify content
        self.assertIn('<!DOCTYPE html>', html_content)
        self.assertIn('<title>Test Document</title>', html_content)
        self.assertIn('<h1>Test Document</h1>', html_content)
        self.assertIn('<div class=\'metadata\'>', html_content)
        self.assertIn('<p>This is a paragraph on page 1.</p>', html_content)
        self.assertIn('<table>', html_content)
        self.assertIn('<th>Header 1</th>', html_content)
        self.assertIn('<td>Data 1</td>', html_content)
        self.assertIn('<img src=', html_content)
        self.assertIn('<figcaption class=\'caption\'>Test Image</figcaption>', html_content)
        self.assertIn('<div class=\'page-break\'>Page 2</div>', html_content)
    
    def test_format_with_custom_config(self):
        """Test formatting document with custom configuration."""
        # Create formatter with custom config
        custom_formatter = OutputFormatter({
            'include_metadata': False,
            'include_page_breaks': False,
            'include_captions': False,
            'image_base_url': 'https://example.com/images'
        })
        
        # Format the document as JSON
        formatted_output_file = custom_formatter.save_formatted_output(
            self.test_document,
            self.output_dir,
            'json'
        )
        
        # Check if file exists
        self.assertTrue(formatted_output_file.exists())
        
        # Check file content
        with open(formatted_output_file, 'r', encoding='utf-8') as f:
            formatted_data = json.load(f)
            
        # Check content for page breaks (should not be present)
        page_breaks = [item for item in formatted_data['content'] if item.get('type') == 'page_break']
        self.assertEqual(len(page_breaks), 0)
        
        # Check image URLs if there are any images
        images = [item for item in formatted_data['content'] if item.get('type') == 'image']
        for image in images:
            if 'url' in image and image['url']:
                self.assertTrue(image['url'].startswith('https://example.com/images'))


class TestSQLFormatterIntegration(unittest.TestCase):
    """Integration tests for the SQLFormatter with sample document data."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Create a sample document for testing
        self.test_document = MagicMock()
        self.test_document.name = "test_document"
        self.test_document.metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "keywords": ["test", "document", "sql"],
            "created": "2023-01-01"
        }
        
        # Mock pages content
        pages = []
        
        # Create page 1 with text and image
        page1 = MagicMock()
        page1.page_number = 1
        page1.segments = [
            MagicMock(text="This is paragraph 1."),
            MagicMock(text="This is paragraph 2.")
        ]
        page1.images = [MagicMock(
            id="img1",
            path="images/img1.png",
            caption="Test Image",
            width=100,
            height=100
        )]
        pages.append(page1)
        
        # Create page 2 with a table
        page2 = MagicMock()
        page2.page_number = 2
        page2.segments = [MagicMock(text="This is page 2 text.")]
        
        # Mock table with cells
        table_mock = MagicMock()
        table_mock.caption = "Test Table"
        table_mock.cells = [
            {"row": 0, "col": 0, "text": "Header 1"},
            {"row": 0, "col": 1, "text": "Header 2"},
            {"row": 1, "col": 0, "text": "Data 1"},
            {"row": 1, "col": 1, "text": "Data 2"}
        ]
        page2.tables = [table_mock]
        pages.append(page2)
        
        # Add pages to document
        self.test_document.pages = pages
        
        # Import SQLFormatter here to ensure we're testing the right module
        from src.sql_formatter import SQLFormatter
        self.formatter = SQLFormatter()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_format_as_sql_json(self):
        """Test the basic SQL JSON formatting"""
        # Format the document
        formatted_data = self.formatter.format_as_sql_json(self.test_document)
        
        # Verify basic structure
        self.assertIn("source", formatted_data)
        self.assertIn("furniture", formatted_data)
        self.assertIn("chunks", formatted_data)
        
        # Verify source information
        self.assertEqual(formatted_data["source"]["file_name"], "test_document.pdf")
        self.assertEqual(formatted_data["source"]["title"], "Test Document")
        
        # Verify furniture contains metadata
        self.assertIn("title", formatted_data["furniture"])
        self.assertEqual(formatted_data["furniture"]["title"], "Test Document")
        
        # Verify chunks content
        chunks = formatted_data["chunks"]
        self.assertTrue(len(chunks) > 0)
        
        # Check that paragraphs are in chunks
        paragraph_chunks = [c for c in chunks if "This is paragraph" in c.get("text", "")]
        self.assertTrue(len(paragraph_chunks) > 0)
        
        # Check that each chunk has required fields
        for chunk in chunks:
            self.assertIn("text", chunk)
            self.assertIn("start_page", chunk)
            self.assertIn("file_path", chunk)
    
    def test_save_sql_output(self):
        """Test saving SQL-formatted output to a file"""
        # Format and save the document
        output_file = self.formatter.save_formatted_output(self.test_document, self.output_dir)
        
        # Verify the file exists
        self.assertTrue(output_file.exists())
        
        # Verify file extension
        self.assertTrue(output_file.name.endswith('.json'))
        
        # Check content
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        # Verify structure
        self.assertIn("source", saved_data)
        self.assertIn("furniture", saved_data)
        self.assertIn("chunks", saved_data)
    
    @patch('src.parse_helper.process_pdf_document')
    def test_integration_with_parse_main(self, mock_process_pdf):
        """Test integration with parse_main.py"""
        # Configure the mock to return our test document
        mock_process_pdf.return_value = self.test_document
        
        # Run parse_main with SQL format
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), '../src/parse_main.py'),
            '--pdf_path', 'test.pdf',
            '--output_dir', str(self.output_dir),
            '--output_format', 'sql'
        ]
        
        # Use a subprocess to run the command
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            # Check for successful execution
            self.assertEqual(result.returncode, 0, f"Command failed with: {result.stderr}")
            
            # Check if output file exists
            output_file = self.output_dir / "test_document.json"
            self.assertTrue(output_file.exists(), f"Output file not found: {output_file}")
            
            # Verify content
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.assertIn("source", data)
            self.assertIn("furniture", data)
            self.assertIn("chunks", data)
            
        except subprocess.TimeoutExpired:
            self.fail("Command timed out")
    
    def test_structure_and_fields(self):
        """Test that SQL formatter includes all required fields"""
        # Format the document
        formatted_data = self.formatter.format_as_sql_json(self.test_document)
        
        # Check source fields
        source = formatted_data["source"]
        self.assertIn("file_name", source)
        self.assertIn("file_path", source)
        self.assertIn("title", source)
        self.assertIn("date", source)
        
        # Check furniture fields
        furniture = formatted_data["furniture"]
        self.assertIn("title", furniture)
        self.assertIn("date", furniture)
        self.assertIn("file_path", furniture)
        
        # Check chunk fields
        for chunk in formatted_data["chunks"]:
            self.assertIn("text", chunk)
            self.assertIn("start_page", chunk)
            self.assertIn("file_path", chunk)
            self.assertIn("date", chunk)
            self.assertIn("title", chunk)


if __name__ == "__main__":
    unittest.main() 