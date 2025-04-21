"""
PDF Image Extraction Module

This module provides functionality to extract images from PDF documents using 
the docling library. It handles image extraction, metadata capture, and 
integration with the existing element map structure.
"""

import base64
import io
import logging
import os
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, BinaryIO
import uuid

# Import docling library components
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.document import ConversionResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFImageExtractor:
    """
    Extracts images from PDF documents using the docling library.
    
    This class provides methods to extract images from PDF documents,
    capture their metadata, and store references to their original locations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the PDF image extractor with optional configuration.
        
        Args:
            config: Optional configuration dictionary with settings
        """
        self.config = config or {}
        self._setup_pipeline_options()
        
    def _setup_pipeline_options(self) -> None:
        """Set up the PDF pipeline options for image extraction."""
        # Create PDF pipeline options optimized for image extraction
        self.pipeline_options = PdfPipelineOptions()
        
        # Enable image generation
        self.pipeline_options.images_scale = self.config.get('images_scale', 2.0)
        self.pipeline_options.generate_page_images = True
        self.pipeline_options.generate_picture_images = True
        
        # Enable picture description if specified in config
        self.pipeline_options.do_picture_description = self.config.get('do_picture_description', True)
        
        # Enable table structure extraction if specified in config
        self.pipeline_options.do_table_structure = self.config.get('do_table_structure', True)
        
        # Allow external plugins if specified
        self.pipeline_options.allow_external_plugins = self.config.get('allow_external_plugins', True)
        
        # Additional options can be configured here
        
    def extract_images(self, pdf_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract images from a PDF document.
        
        Args:
            pdf_path: Path to the PDF document
            
        Returns:
            A dictionary containing extracted images and their metadata
        
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            RuntimeError: If there's an error during extraction
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        logger.info(f"Extracting images from PDF: {pdf_path}")
        
        try:
            # Create a DocumentConverter with PDF format option
            doc_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=self.pipeline_options)
                }
            )
            
            # Convert the PDF document
            conversion_result = doc_converter.convert(pdf_path)
            
            # Check conversion status
            if conversion_result.status != "success":
                raise RuntimeError(f"PDF conversion failed: {conversion_result.status}")
                
            # Extract images from the conversion result
            images_data = self._extract_images_from_result(conversion_result)
            
            logger.info(f"Successfully extracted {len(images_data)} images from {pdf_path}")
            return images_data
            
        except Exception as e:
            logger.exception(f"Error extracting images from PDF: {e}")
            raise RuntimeError(f"Failed to extract images: {e}")
            
    def _extract_images_from_result(self, conversion_result: ConversionResult) -> Dict[str, Any]:
        """
        Extract images from the conversion result.
        
        Args:
            conversion_result: The docling conversion result
            
        Returns:
            A dictionary containing extracted images and their metadata
        """
        docling_document = conversion_result.document
        images_data = {
            "document_name": getattr(docling_document, 'name', 'Unknown'),
            "total_pages": len(getattr(docling_document, 'pages', [])),
            "images": []
        }
        
        # Process all pictures in the document
        if hasattr(docling_document, 'pictures') and docling_document.pictures:
            for i, picture in enumerate(docling_document.pictures):
                # Extract image data and metadata
                image_data = self._process_picture(picture, i, docling_document)
                if image_data:
                    images_data["images"].append(image_data)
        
        return images_data
        
    def _process_picture(self, picture: Any, index: int, document: Any) -> Dict[str, Any]:
        """
        Process a picture element from the document.
        
        Args:
            picture: The picture element
            index: The picture index
            document: The docling document
            
        Returns:
            A dictionary containing the image data and metadata
        """
        try:
            # Create a unique identifier for the image
            image_id = f"picture_{index + 1}"
            
            # Extract image metadata
            metadata = {
                "id": image_id,
                "docling_ref": getattr(picture, 'self_ref', f"#/pictures/{index}"),
                "page_number": self._get_picture_page_number(picture, document),
                "bounds": getattr(picture, 'bounds', None),
                "description": getattr(picture, 'description', ''),
                "format": self._determine_image_format(picture),
                "size": self._get_picture_size(picture),
            }
            
            # Extract image data
            image_data = None
            if hasattr(picture, 'image_data') and picture.image_data:
                image_data = picture.image_data
            elif hasattr(picture, 'image_path') and picture.image_path:
                # Load image data from path if available
                try:
                    with open(picture.image_path, 'rb') as img_file:
                        image_data = img_file.read()
                except Exception as e:
                    logger.warning(f"Failed to read image from path {picture.image_path}: {e}")
            
            # Convert image data to base64 if available
            if image_data:
                base64_data = base64.b64encode(image_data).decode('utf-8')
                mime_type = metadata["format"] or "image/png"
                data_uri = f"data:{mime_type};base64,{base64_data}"
                
                return {
                    "metadata": metadata,
                    "data_uri": data_uri,
                    "raw_data": image_data,  # Can be used for external storage
                }
            else:
                logger.warning(f"No image data found for picture {image_id}")
                return {
                    "metadata": metadata,
                    "data_uri": None,
                    "raw_data": None,
                }
                
        except Exception as e:
            logger.warning(f"Error processing image {index}: {e}")
            return None
            
    def _get_picture_page_number(self, picture: Any, document: Any) -> Optional[int]:
        """Get the page number for a picture."""
        # Try to get page number from picture object
        if hasattr(picture, 'page_number'):
            return picture.page_number
        
        # Try to get page number from picture metadata
        if hasattr(picture, 'metadata') and hasattr(picture.metadata, 'page_number'):
            return picture.metadata.page_number
        
        # Try to determine from prov data if available
        if hasattr(picture, 'prov') and hasattr(picture.prov, 'page_no'):
            return picture.prov.page_no
            
        # As a fallback, try to find the image in pages
        if hasattr(document, 'pages'):
            for i, page in enumerate(document.pages):
                if hasattr(page, 'pictures') and page.pictures:
                    for p in page.pictures:
                        if p is picture or getattr(p, 'self_ref', None) == getattr(picture, 'self_ref', None):
                            return i + 1
        
        return None
        
    def _determine_image_format(self, picture: Any) -> Optional[str]:
        """Determine the image format/MIME type."""
        # Try to get from metadata
        if hasattr(picture, 'metadata') and hasattr(picture.metadata, 'format'):
            return picture.metadata.format
            
        # Try to determine from image path
        if hasattr(picture, 'image_path') and picture.image_path:
            ext = os.path.splitext(picture.image_path)[1].lower()
            return mimetypes.guess_type(f"image{ext}")[0]
            
        # Default to PNG if unknown
        return "image/png"
        
    def _get_picture_size(self, picture: Any) -> Dict[str, Optional[int]]:
        """Get the picture size (width and height)."""
        width = None
        height = None
        
        # Try to get from bounds
        if hasattr(picture, 'bounds'):
            bounds = picture.bounds
            if bounds:
                width = getattr(bounds, 'width', None)
                height = getattr(bounds, 'height', None)
                
                # If not directly available, try to calculate from coordinates
                if width is None and hasattr(bounds, 'right') and hasattr(bounds, 'left'):
                    width = bounds.right - bounds.left
                if height is None and hasattr(bounds, 'bottom') and hasattr(bounds, 'top'):
                    height = bounds.bottom - bounds.top
        
        # Try to get from size attribute
        if width is None and hasattr(picture, 'size'):
            width = getattr(picture.size, 'width', None)
            height = getattr(picture.size, 'height', None)
            
        return {
            "width": width,
            "height": height
        }


class ImageContentRelationship:
    """
    Maintains relationships between images and their surrounding text content.
    
    This class provides methods to analyze and store relationships between
    images and related text elements in the document.
    """
    
    def __init__(self, element_map: Dict[str, Any], flattened_sequence: List[Dict[str, Any]]):
        """
        Initialize with the element map and flattened document sequence.
        
        Args:
            element_map: The document element map
            flattened_sequence: The flattened document sequence in reading order
        """
        self.element_map = element_map
        self.flattened_sequence = flattened_sequence
        self.relationships = {}
        
    def analyze_relationships(self, images_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze relationships between images and text content.
        
        Args:
            images_data: The images data from PDFImageExtractor
            
        Returns:
            Updated images data with relationship information
        """
        if not images_data or not images_data.get("images"):
            return images_data
            
        # Process each image
        for image in images_data["images"]:
            image_id = image["metadata"]["id"]
            docling_ref = image["metadata"]["docling_ref"]
            
            # Find references to this image in the document
            references = self._find_image_references(docling_ref)
            
            # Find surrounding text
            context_before, context_after = self._find_surrounding_text(docling_ref)
            
            # Find potential captions
            caption = self._find_caption(docling_ref)
            
            # Update image with relationship data
            if "context" not in image:
                image["context"] = {}
                
            image["context"].update({
                "references": references,
                "text_before": context_before,
                "text_after": context_after,
                "caption": caption
            })
            
            # Store relationship in the relationships dictionary
            self.relationships[image_id] = {
                "image": image,
                "references": references,
                "context_before": context_before,
                "context_after": context_after,
                "caption": caption
            }
            
        # Add relationship map to images_data
        images_data["relationships"] = self.relationships
        return images_data
        
    def _find_image_references(self, image_ref: str) -> List[Dict[str, Any]]:
        """Find references to the image in the document."""
        references = []
        
        # Look for elements that reference this image
        for element_id, element in self.element_map.items():
            # Skip if it's the image itself
            if element_id == image_ref:
                continue
                
            # Check for references in various fields
            found_reference = False
            
            # Check direct references
            if hasattr(element, 'ref') and element.ref == image_ref:
                found_reference = True
                
            # Check for references in $ref fields
            elif isinstance(element, dict):
                for key, value in element.items():
                    if isinstance(value, dict) and value.get('$ref') == image_ref:
                        found_reference = True
                        break
            
            if found_reference:
                references.append({
                    "element_id": element_id,
                    "element_type": element.get('metadata', {}).get('type', 'unknown') 
                                    if isinstance(element, dict) else 'unknown'
                })
                
        return references
        
    def _find_surrounding_text(self, image_ref: str) -> Tuple[str, str]:
        """Find text before and after the image in the document sequence."""
        context_before = ""
        context_after = ""
        
        # Find the image position in the sequence
        image_index = -1
        for i, element in enumerate(self.flattened_sequence):
            element_id = element.get('id', element.get('self_ref', None))
            if element_id == image_ref:
                image_index = i
                break
                
        if image_index == -1:
            return context_before, context_after
            
        # Get text before the image
        i = image_index - 1
        remaining_chars = 100  # Get up to 100 characters
        while i >= 0 and remaining_chars > 0:
            element = self.flattened_sequence[i]
            if isinstance(element, dict) and element.get('metadata', {}).get('type') == 'paragraph':
                text = element.get('text', '')
                if text:
                    if len(text) <= remaining_chars:
                        context_before = text + ' ' + context_before
                        remaining_chars -= len(text)
                    else:
                        context_before = text[-remaining_chars:] + ' ' + context_before
                        remaining_chars = 0
            i -= 1
            
        # Get text after the image
        i = image_index + 1
        remaining_chars = 100  # Get up to 100 characters
        while i < len(self.flattened_sequence) and remaining_chars > 0:
            element = self.flattened_sequence[i]
            if isinstance(element, dict) and element.get('metadata', {}).get('type') == 'paragraph':
                text = element.get('text', '')
                if text:
                    if len(text) <= remaining_chars:
                        context_after = context_after + ' ' + text
                        remaining_chars -= len(text)
                    else:
                        context_after = context_after + ' ' + text[:remaining_chars]
                        remaining_chars = 0
            i += 1
            
        return context_before.strip(), context_after.strip()
        
    def _find_caption(self, image_ref: str) -> Optional[str]:
        """Find a caption for the image."""
        caption = None
        
        # Look for caption patterns in the sequence
        image_index = -1
        for i, element in enumerate(self.flattened_sequence):
            element_id = element.get('id', element.get('self_ref', None))
            if element_id == image_ref:
                image_index = i
                break
                
        if image_index == -1:
            return caption
            
        # Check elements after the image for potential captions
        # Usually captions are within 1-2 elements after the image
        for i in range(image_index + 1, min(image_index + 3, len(self.flattened_sequence))):
            element = self.flattened_sequence[i]
            if isinstance(element, dict):
                text = element.get('text', '')
                element_type = element.get('metadata', {}).get('type', '')
                
                # Captions often start with "Figure", "Fig.", or similar
                if text and (text.startswith("Figure") or text.startswith("Fig.") or 
                             element_type == 'caption' or 'caption' in element_type.lower()):
                    caption = text
                    break
                    
        return caption


# Utility functions for image processing
class ImageProcessor:
    """
    Utility class for basic image processing operations.
    
    Provides static methods for image resizing, format conversion,
    quality enhancement, and metadata extraction.
    """
    
    @staticmethod
    def resize_image(image_data: bytes, width: int, height: int) -> bytes:
        """
        Resize an image to the specified dimensions.
        
        Args:
            image_data: The binary image data
            width: Target width
            height: Target height
            
        Returns:
            Resized image binary data
            
        Raises:
            ImportError: If PIL is not installed
            ValueError: If the image data is invalid
        """
        try:
            from PIL import Image
        except ImportError:
            logger.error("PIL is required for image resizing. Install with 'pip install Pillow'")
            raise ImportError("PIL is required for image processing")
            
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                resized_img = img.resize((width, height), Image.LANCZOS)
                output = io.BytesIO()
                img_format = img.format or 'PNG'
                resized_img.save(output, format=img_format)
                return output.getvalue()
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            raise ValueError(f"Invalid image data: {e}")
            
    @staticmethod
    def convert_format(image_data: bytes, target_format: str) -> bytes:
        """
        Convert an image to a different format.
        
        Args:
            image_data: The binary image data
            target_format: Target format (e.g., 'JPEG', 'PNG', 'TIFF')
            
        Returns:
            Converted image binary data
            
        Raises:
            ImportError: If PIL is not installed
            ValueError: If the image data or format is invalid
        """
        try:
            from PIL import Image
        except ImportError:
            logger.error("PIL is required for image conversion. Install with 'pip install Pillow'")
            raise ImportError("PIL is required for image processing")
            
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                output = io.BytesIO()
                img.save(output, format=target_format)
                return output.getvalue()
        except Exception as e:
            logger.error(f"Error converting image format: {e}")
            raise ValueError(f"Invalid image data or format: {e}")
            
    @staticmethod
    def enhance_quality(image_data: bytes, contrast: float = 1.2, brightness: float = 1.1) -> bytes:
        """
        Enhance image quality by adjusting contrast and brightness.
        
        Args:
            image_data: The binary image data
            contrast: Contrast enhancement factor
            brightness: Brightness enhancement factor
            
        Returns:
            Enhanced image binary data
            
        Raises:
            ImportError: If PIL is not installed
            ValueError: If the image data is invalid
        """
        try:
            from PIL import Image, ImageEnhance
        except ImportError:
            logger.error("PIL is required for image enhancement. Install with 'pip install Pillow'")
            raise ImportError("PIL is required for image processing")
            
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # Enhance contrast
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(contrast)
                
                # Enhance brightness
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(brightness)
                
                output = io.BytesIO()
                img_format = img.format or 'PNG'
                img.save(output, format=img_format)
                return output.getvalue()
        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            raise ValueError(f"Invalid image data: {e}")
            
    @staticmethod
    def extract_metadata(image_data: bytes) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from an image.
        
        Args:
            image_data: The binary image data
            
        Returns:
            Dictionary containing image metadata
            
        Raises:
            ImportError: If PIL is not installed
            ValueError: If the image data is invalid
        """
        try:
            from PIL import Image, ExifTags
        except ImportError:
            logger.error("PIL is required for metadata extraction. Install with 'pip install Pillow'")
            raise ImportError("PIL is required for image processing")
            
        metadata = {}
        
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # Basic metadata
                metadata.update({
                    "format": img.format,
                    "mode": img.mode,
                    "size": {
                        "width": img.width,
                        "height": img.height
                    }
                })
                
                # EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif = {}
                    for tag, value in img._getexif().items():
                        if tag in ExifTags.TAGS:
                            exif[ExifTags.TAGS[tag]] = value
                    metadata["exif"] = exif
                    
                # Other image metadata
                for key, value in img.info.items():
                    if key != 'exif':  # Already handled above
                        metadata[key] = value
                        
                return metadata
        except Exception as e:
            logger.error(f"Error extracting image metadata: {e}")
            raise ValueError(f"Invalid image data: {e}")


# Custom exceptions for different error scenarios
class ImageExtractionError(Exception):
    """Base class for image extraction errors."""
    pass

class CorruptedImageError(ImageExtractionError):
    """Error raised when an image is corrupted."""
    pass

class UnsupportedFormatError(ImageExtractionError):
    """Error raised when an image format is not supported."""
    pass

class ExtractionFailureError(ImageExtractionError):
    """Error raised when image extraction fails."""
    pass

class PermissionError(ImageExtractionError):
    """Error raised when there are permission issues."""
    pass


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_image_extractor.py <path_to_pdf>")
        sys.exit(1)
        
    # Create a PDF image extractor
    extractor = PDFImageExtractor()
    
    try:
        # Extract images from PDF
        images_data = extractor.extract_images(sys.argv[1])
        
        # Print summary
        print(f"Found {len(images_data['images'])} images in {images_data['document_name']}")
        
        # Process each image
        for i, image in enumerate(images_data['images']):
            metadata = image['metadata']
            print(f"Image {i+1}:")
            print(f"  ID: {metadata['id']}")
            print(f"  Page: {metadata['page_number']}")
            print(f"  Format: {metadata['format']}")
            print(f"  Size: {metadata['size']['width']}x{metadata['size']['height']}")
            
        # Save to JSON for debugging
        import json
        output_file = 'extracted_images.json'
        with open(output_file, 'w') as f:
            # Remove binary data for JSON output
            output_data = {**images_data}
            for img in output_data['images']:
                img.pop('raw_data', None)
            json.dump(output_data, f, indent=2)
            
        print(f"Image data saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 