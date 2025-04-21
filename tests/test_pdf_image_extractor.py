"""
Tests for the PDF Image Extractor Module

This module contains tests for the PDFImageExtractor class that extracts
images from PDF documents using the docling library.
"""

import os
import sys
import pytest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import base64
import io
import json

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the module to test
from pdf_image_extractor import PDFImageExtractor, ImageContentRelationship, ImageProcessor
from pdf_image_extractor import CorruptedImageError, UnsupportedFormatError, ExtractionFailureError

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPDFImageExtractor:
    """Tests for the PDFImageExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a test PDF path
        test_data_dir = Path('../test_data')
        if test_data_dir.exists():
            test_pdf_files = list(test_data_dir.glob('*.pdf'))
            self.test_pdf_path = test_pdf_files[0] if test_pdf_files else None
        else:
            self.test_pdf_path = None
            
        # Create a configuration for testing
        self.test_config = {
            'images_scale': 1.5,
            'do_picture_description': True,
            'do_table_structure': True,
            'allow_external_plugins': True
        }
        
        # Create an instance of the extractor
        self.extractor = PDFImageExtractor(config=self.test_config)
    
    def test_initialization(self):
        """Test initialization of the PDFImageExtractor."""
        # Test with default config
        extractor = PDFImageExtractor()
        assert extractor.config == {}
        assert hasattr(extractor, 'pipeline_options')
        
        # Test with custom config
        extractor = PDFImageExtractor(config=self.test_config)
        assert extractor.config == self.test_config
        assert extractor.pipeline_options.images_scale == self.test_config['images_scale']
        assert extractor.pipeline_options.do_picture_description is True
        assert extractor.pipeline_options.generate_picture_images is True
    
    @pytest.mark.skipif(not Path('../test_data').exists() or not list(Path('../test_data').glob('*.pdf')), 
                        reason="No test PDF files found in test_data directory")
    def test_extract_images_with_real_pdf(self):
        """Test extracting images from a real PDF file."""
        # This test will be skipped if no test PDFs are available
        assert self.test_pdf_path is not None
        
        # Extract images from the test PDF
        images_data = self.extractor.extract_images(self.test_pdf_path)
        
        # Basic validation of the result structure
        assert isinstance(images_data, dict)
        assert "document_name" in images_data
        assert "total_pages" in images_data
        assert "images" in images_data
        
        # Log the number of images found
        logger.info(f"Found {len(images_data['images'])} images in test PDF")
    
    @patch('pdf_image_extractor.DocumentConverter')
    def test_extract_images_with_mock(self, mock_converter_class):
        """Test extracting images with mocked docling library."""
        # Create a mock conversion result
        mock_conversion_result = MagicMock()
        mock_conversion_result.status = "success"
        
        # Create a mock document
        mock_document = MagicMock()
        mock_document.name = "Test Document"
        mock_document.pages = [MagicMock(), MagicMock()]  # Two pages
        
        # Create a mock picture
        mock_picture = MagicMock()
        mock_picture.self_ref = "#/pictures/0"
        mock_picture.bounds = MagicMock()
        mock_picture.bounds.width = 100
        mock_picture.bounds.height = 200
        mock_picture.description = "A test image"
        
        # Create some mock image data
        # A small 1x1 PNG image as base64
        mock_image_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4//8/AAX+Av7czFnnAAAAAElFTkSuQmCC"
        )
        mock_picture.image_data = mock_image_data
        
        # Add the picture to the document
        mock_document.pictures = [mock_picture]
        
        # Set the document on the conversion result
        mock_conversion_result.document = mock_document
        
        # Configure the mock converter
        mock_converter_instance = MagicMock()
        mock_converter_instance.convert.return_value = mock_conversion_result
        mock_converter_class.return_value = mock_converter_instance
        
        # Create a temporary file path for the test
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
            # Extract images
            images_data = self.extractor.extract_images(temp_file.name)
            
            # Verify the converter was called correctly
            mock_converter_class.assert_called_once()
            mock_converter_instance.convert.assert_called_once()
            
            # Verify the result structure
            assert images_data["document_name"] == "Test Document"
            assert images_data["total_pages"] == 2
            assert len(images_data["images"]) == 1
            
            # Verify the image data
            image = images_data["images"][0]
            assert image["metadata"]["id"] == "picture_1"
            assert image["metadata"]["docling_ref"] == "#/pictures/0"
            assert image["metadata"]["size"]["width"] == 100
            assert image["metadata"]["size"]["height"] == 200
            assert "data_uri" in image
            assert image["data_uri"].startswith("data:image/png;base64,")
    
    def test_file_not_found_error(self):
        """Test that FileNotFoundError is raised for non-existent PDF."""
        non_existent_path = Path("non_existent_file.pdf")
        
        with pytest.raises(FileNotFoundError):
            self.extractor.extract_images(non_existent_path)
    
    @patch('pdf_image_extractor.DocumentConverter')
    def test_conversion_failure(self, mock_converter_class):
        """Test handling of conversion failure."""
        # Create a mock conversion result with failure status
        mock_conversion_result = MagicMock()
        mock_conversion_result.status = "failure"
        
        # Configure the mock converter
        mock_converter_instance = MagicMock()
        mock_converter_instance.convert.return_value = mock_conversion_result
        mock_converter_class.return_value = mock_converter_instance
        
        # Create a temporary file path for the test
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
            # Extract images - should raise RuntimeError
            with pytest.raises(RuntimeError):
                self.extractor.extract_images(temp_file.name)


class TestImageContentRelationship:
    """Tests for the ImageContentRelationship class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock element map
        self.element_map = {
            "#/pictures/0": {
                "id": "#/pictures/0",
                "metadata": {"type": "picture"},
                "bounds": {"width": 100, "height": 200}
            },
            "#/texts/0": {
                "id": "#/texts/0",
                "metadata": {"type": "paragraph"},
                "text": "This is text before the image."
            },
            "#/texts/1": {
                "id": "#/texts/1",
                "metadata": {"type": "paragraph"},
                "text": "This is text after the image."
            },
            "#/texts/2": {
                "id": "#/texts/2",
                "metadata": {"type": "caption"},
                "text": "Figure 1: Test image caption"
            },
            "#/texts/3": {
                "id": "#/texts/3",
                "metadata": {"type": "paragraph"},
                "ref": "#/pictures/0",  # Reference to the image
                "text": "As shown in the figure above..."
            }
        }
        
        # Create a flattened sequence
        self.flattened_sequence = [
            self.element_map["#/texts/0"],
            self.element_map["#/pictures/0"],
            self.element_map["#/texts/2"],  # Caption
            self.element_map["#/texts/1"],
            self.element_map["#/texts/3"]
        ]
        
        # Create an image relationship analyzer
        self.relationship = ImageContentRelationship(
            self.element_map,
            self.flattened_sequence
        )
        
        # Create test images data
        self.images_data = {
            "document_name": "Test Document",
            "total_pages": 1,
            "images": [
                {
                    "metadata": {
                        "id": "picture_1",
                        "docling_ref": "#/pictures/0",
                        "page_number": 1,
                        "format": "image/png",
                        "size": {"width": 100, "height": 200}
                    },
                    "data_uri": "data:image/png;base64,..."
                }
            ]
        }
    
    def test_analyze_relationships(self):
        """Test analyzing relationships between images and text."""
        # Analyze relationships
        result = self.relationship.analyze_relationships(self.images_data)
        
        # Verify relationships were added
        assert "relationships" in result
        
        # Verify the specific image relationships
        image_id = "picture_1"
        assert image_id in result["relationships"]
        
        # Check image context was updated
        assert "context" in result["images"][0]
        context = result["images"][0]["context"]
        
        # Check text before/after
        assert "text_before" in context
        assert context["text_before"] == "This is text before the image."
        
        # Check caption
        assert "caption" in context
        assert context["caption"] == "Figure 1: Test image caption"
        
        # Check references
        assert "references" in context
        assert len(context["references"]) == 1
        assert context["references"][0]["element_id"] == "#/texts/3"


class TestImageProcessor:
    """Tests for the ImageProcessor utility class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a small test image
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL is required for these tests")
            
        # Create a small 10x10 test image
        self.test_image = Image.new('RGB', (10, 10), color='red')
        self.image_buffer = io.BytesIO()
        self.test_image.save(self.image_buffer, format='PNG')
        self.image_data = self.image_buffer.getvalue()
    
    def test_resize_image(self):
        """Test image resizing functionality."""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL is required for these tests")
            
        # Resize the image
        resized_data = ImageProcessor.resize_image(self.image_data, 20, 15)
        
        # Verify the resized image
        with Image.open(io.BytesIO(resized_data)) as img:
            assert img.width == 20
            assert img.height == 15
    
    def test_convert_format(self):
        """Test image format conversion."""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL is required for these tests")
            
        # Convert to JPEG
        jpeg_data = ImageProcessor.convert_format(self.image_data, 'JPEG')
        
        # Verify the format
        with Image.open(io.BytesIO(jpeg_data)) as img:
            assert img.format == 'JPEG'
    
    def test_extract_metadata(self):
        """Test metadata extraction."""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL is required for these tests")
            
        # Extract metadata
        metadata = ImageProcessor.extract_metadata(self.image_data)
        
        # Verify basic metadata
        assert metadata["format"] == "PNG"
        assert metadata["size"]["width"] == 10
        assert metadata["size"]["height"] == 10
        
    def test_enhance_quality(self):
        """Test image quality enhancement."""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL is required for these tests")
            
        # Enhance image quality
        enhanced_data = ImageProcessor.enhance_quality(
            self.image_data, 
            contrast=1.2, 
            brightness=1.1
        )
        
        # Basic verification that we got image data back
        assert len(enhanced_data) > 0
        
        # Verify it's a valid image
        with Image.open(io.BytesIO(enhanced_data)) as img:
            assert img.width == 10
            assert img.height == 10


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 