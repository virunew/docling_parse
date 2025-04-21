"""
Integration Tests for PDF Image Extraction with parse_main.py

This module tests the integration of the PDF Image Extractor module with
the main parsing program (parse_main.py).
"""

import os
import sys
import pytest
import logging
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the modules to test
import parse_main
from pdf_image_extractor import PDFImageExtractor, ImageContentRelationship

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPDFImageExtractionIntegration:
    """Integration tests for PDF Image Extraction with parse_main.py."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Find a test PDF if available
        test_data_dir = Path('../test_data')
        if test_data_dir.exists():
            test_pdf_files = list(test_data_dir.glob('*.pdf'))
            self.test_pdf_path = test_pdf_files[0] if test_pdf_files else None
        else:
            self.test_pdf_path = None
            
        # Create output directory
        self.output_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up after tests."""
        # Clean up temporary files and directories
        if hasattr(self, 'output_dir') and os.path.exists(self.output_dir):
            # In a real cleanup, we would remove files, but for testing we'll keep them
            pass
    
    @pytest.mark.skipif(not Path('../test_data').exists() or not list(Path('../test_data').glob('*.pdf')), 
                        reason="No test PDF files found in test_data directory")
    def test_process_pdf_document_returns_docling_document(self):
        """Test that process_pdf_document returns a DoclingDocument object."""
        # Skip if no test PDF is available
        if not self.test_pdf_path:
            pytest.skip("No test PDF file available")
            
        # Process the PDF using parse_main.process_pdf_document
        docling_document = parse_main.process_pdf_document(
            self.test_pdf_path, 
            self.output_dir
        )
        
        # Verify we got a document back
        assert docling_document is not None
        
        # Verify the document has expected attributes
        assert hasattr(docling_document, 'pages')
        
        # Verify the document contains some content
        assert len(docling_document.pages) > 0
        
        logger.info(f"Successfully processed PDF with {len(docling_document.pages)} pages")
        
    @pytest.mark.skipif(not Path('../test_data').exists() or not list(Path('../test_data').glob('*.pdf')), 
                        reason="No test PDF files found in test_data directory")
    def test_extract_images_from_processed_document(self):
        """Test extracting images from a document processed by parse_main."""
        # Skip if no test PDF is available
        if not self.test_pdf_path:
            pytest.skip("No test PDF file available")
            
        # Process the PDF using parse_main.process_pdf_document
        docling_document = parse_main.process_pdf_document(
            self.test_pdf_path, 
            self.output_dir
        )
        
        # Now extract images from the document using our PDFImageExtractor
        # We need to convert the docling_document to a dict first
        doc_dict = docling_document.export_to_dict()
        
        # Save it as JSON temporarily to simulate normal workflow
        temp_json_path = os.path.join(self.output_dir, "temp_doc.json")
        with open(temp_json_path, 'w') as f:
            json.dump(doc_dict, f)
            
        # Create an extractor to extract images from the processed document
        extractor = PDFImageExtractor()
        
        # This test might fail depending on how PDFImageExtractor processes the document
        # We're patching extract_images to use our saved JSON instead of processing a PDF directly
        with patch.object(PDFImageExtractor, 'extract_images') as mock_extract:
            # Configure the mock to call a helper method that processes our JSON
            def process_json_helper(pdf_path):
                # Create a mock ConversionResult
                mock_conversion_result = MagicMock()
                mock_conversion_result.status = "success"
                
                # Use the real docling_document from parse_main
                mock_conversion_result.document = docling_document
                
                # Call the real implementation for extraction
                return extractor._extract_images_from_result(mock_conversion_result)
                
            mock_extract.side_effect = process_json_helper
            
            # Now call extract_images (which will use our mocked version)
            images_data = extractor.extract_images(self.test_pdf_path)
            
            # Verify we got image data back
            assert images_data is not None
            assert "document_name" in images_data
            assert "total_pages" in images_data
            assert "images" in images_data
            
            # Log what we found
            logger.info(f"Found {len(images_data['images'])} images in the document")
            
            # If there are images, check their structure
            if images_data["images"]:
                first_image = images_data["images"][0]
                assert "metadata" in first_image
                assert "id" in first_image["metadata"]
                # Data URI might not be available if image extraction fails
                if first_image.get("data_uri"):
                    assert first_image["data_uri"].startswith("data:")
    
    @pytest.mark.skipif(not Path('../test_data').exists() or not list(Path('../test_data').glob('*.pdf')), 
                        reason="No test PDF files found in test_data directory")
    def test_element_map_integration(self):
        """Test integration with element_map_builder."""
        # Skip if no test PDF is available
        if not self.test_pdf_path:
            pytest.skip("No test PDF file available")
            
        # Process the PDF using parse_main.process_pdf_document
        docling_document = parse_main.process_pdf_document(
            self.test_pdf_path, 
            self.output_dir
        )
        
        # Build element map using the element_map_builder function
        from element_map_builder import build_element_map
        element_map = build_element_map(docling_document)
        
        # Verify element map was created
        assert element_map is not None
        assert isinstance(element_map, dict)
        assert len(element_map) > 0
        
        # Now extract images (using our patched method like before)
        extractor = PDFImageExtractor()
        
        with patch.object(PDFImageExtractor, 'extract_images') as mock_extract:
            def process_json_helper(pdf_path):
                mock_conversion_result = MagicMock()
                mock_conversion_result.status = "success"
                mock_conversion_result.document = docling_document
                return extractor._extract_images_from_result(mock_conversion_result)
                
            mock_extract.side_effect = process_json_helper
            
            # Extract images
            images_data = extractor.extract_images(self.test_pdf_path)
            
        # Create flattened sequence (mock for this test)
        # In a real scenario, we'd use get_flattened_body_sequence
        flattened_sequence = list(element_map.values())
        
        # Create image relationship analyzer
        relationship = ImageContentRelationship(element_map, flattened_sequence)
        
        # Analyze relationships
        result = relationship.analyze_relationships(images_data)
        
        # Verify we got relationship data back
        assert "relationships" in result
        
        # Log what we found
        logger.info(f"Found {len(result.get('relationships', {}))} image relationships")
    
    def test_integration_with_mocked_pdf(self):
        """Test integration with a mocked PDF document."""
        # Create mocks for the document processing
        with patch('parse_main.DocumentConverter') as mock_converter_class:
            # Create a mock document with some content
            mock_document = MagicMock()
            mock_document.name = "Test Document"
            mock_document.pages = [MagicMock(), MagicMock()]
            
            # Add a picture to the document
            mock_picture = MagicMock()
            mock_picture.self_ref = "#/pictures/0"
            mock_picture.bounds = MagicMock()
            mock_picture.bounds.width = 100
            mock_picture.bounds.height = 200
            mock_document.pictures = [mock_picture]
            
            # Set up the conversion result
            mock_result = MagicMock()
            mock_result.status = "success"
            mock_result.document = mock_document
            
            # Configure the mock converter
            mock_converter = MagicMock()
            mock_converter.convert.return_value = mock_result
            mock_converter_class.return_value = mock_converter
            
            # Create a temp file for the mock PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
                # Process the PDF
                result_doc = parse_main.process_pdf_document(
                    temp_file.name,
                    self.output_dir
                )
                
                # Verify the result
                assert result_doc is mock_document
                
                # Now test the image extractor
                extractor = PDFImageExtractor()
                
                with patch.object(PDFImageExtractor, '_extract_images_from_result') as mock_extract:
                    # Configure the mock
                    mock_extract.return_value = {
                        "document_name": "Test Document",
                        "total_pages": 2,
                        "images": [
                            {
                                "metadata": {
                                    "id": "picture_1",
                                    "docling_ref": "#/pictures/0",
                                    "page_number": 1,
                                    "size": {"width": 100, "height": 200}
                                }
                            }
                        ]
                    }
                    
                    # Extract images
                    images_data = extractor.extract_images(temp_file.name)
                    
                    # Verify extraction results
                    assert len(images_data["images"]) == 1
                    assert images_data["images"][0]["metadata"]["id"] == "picture_1"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 