"""
PDF Image Extraction Module

This module extends the functionality of the pdf_image_extractor.py module to 
provide enhanced organization of extracted images. It ensures that images are saved
in a directory structure that matches the original file names and provides 
additional utilities for image processing.
"""

import logging
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# Import the existing image extractor functionality
from src.pdf_image_extractor import (
    PDFImageExtractor, 
    ImageContentRelationship, 
    ImageProcessor,
    CorruptedImageError,
    UnsupportedFormatError,
    ExtractionFailureError,
    PermissionError
)

# Configure logging
logger = logging.getLogger(__name__)


class EnhancedImageExtractor:
    """
    Enhanced PDF image extractor that organizes extracted images by file name.
    
    This class builds upon the PDFImageExtractor functionality to ensure that
    extracted images are saved in a directory structure that matches the original
    file names, improving organization and traceability.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced PDF image extractor.
        
        Args:
            config: Optional configuration dictionary with extraction settings
        """
        self.config = config or {}
        self.image_extractor = PDFImageExtractor(self.config)
        
    def extract_and_save_images(
        self, 
        pdf_path: Union[str, Path], 
        output_dir: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Extract images from a PDF document and save them to a file-specific directory.
        
        Args:
            pdf_path: Path to the PDF document
            output_dir: Base directory for saving output
            
        Returns:
            A dictionary containing extracted images data and metadata
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            RuntimeError: If there's an error during extraction
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        logger.info(f"Extracting images from PDF: {pdf_path}")
        
        try:
            # Extract images using the base extractor
            images_data = self.image_extractor.extract_images(pdf_path)
            
            # Create file-specific output directory using the file's stem (name without extension)
            file_output_dir = output_dir / pdf_path.stem
            file_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create images directory within the file-specific directory
            images_dir = file_output_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            logger.info(f"Saving extracted images to {images_dir}")
            
            # Process and save each image
            for i, image in enumerate(images_data.get("images", [])):
                self._save_image(image, i, images_dir, file_output_dir)
                
            # Generate relationship data if element map is available
            element_map_path = file_output_dir / "element_map.json"
            if element_map_path.exists():
                logger.info("Element map found. Generating image relationship data.")
                try:
                    with open(element_map_path, 'r', encoding='utf-8') as f:
                        element_map_data = json.load(f)
                        
                    # Extract needed components from element map
                    flattened_sequence = element_map_data.get("flattened_sequence", [])
                    elements_dict = element_map_data.get("elements", {})
                    
                    if flattened_sequence and elements_dict:
                        # Analyze relationships
                        relationship_analyzer = ImageContentRelationship(
                            elements_dict, 
                            flattened_sequence
                        )
                        enhanced_images_data = relationship_analyzer.analyze_relationships(images_data)
                        
                        # Save the enhanced images data
                        images_data_path = file_output_dir / "images_data.json"
                        with open(images_data_path, 'w', encoding='utf-8') as f:
                            json.dump(enhanced_images_data, f, indent=2)
                            
                        logger.info(f"Image relationship data saved to {images_data_path}")
                        
                        # Update the return data
                        images_data = enhanced_images_data
                except Exception as e:
                    logger.warning(f"Failed to generate relationship data: {e}")
            else:
                logger.info("No element map found. Skipping relationship analysis.")
                
                # Save the basic images data
                images_data_path = file_output_dir / "images_data.json"
                with open(images_data_path, 'w', encoding='utf-8') as f:
                    json.dump(images_data, f, indent=2)
                    
                logger.info(f"Basic image data saved to {images_data_path}")
            
            return images_data
            
        except Exception as e:
            logger.exception(f"Error extracting or saving images: {e}")
            raise RuntimeError(f"Failed to extract or save images: {e}")
    
    def _save_image(
        self, 
        image: Dict[str, Any], 
        index: int, 
        images_dir: Path, 
        parent_dir: Path
    ) -> None:
        """
        Save an extracted image to disk.
        
        Args:
            image: Dictionary containing image data and metadata
            index: Index of the image
            images_dir: Directory to save the image
            parent_dir: Parent directory (for relative path calculation)
        """
        try:
            # Get image data and metadata
            raw_data = image.get("raw_data")
            if not raw_data:
                logger.warning(f"No raw data found for image {index}")
                return
                
            # Extract metadata
            metadata = image.get("metadata", {})
            image_id = metadata.get("id", f"picture_{index + 1}")
            image_format = metadata.get("format", "image/png").split("/")[-1]
            
            # Determine the file path
            image_path = images_dir / f"{image_id}.{image_format}"
            
            # Save the image
            with open(image_path, "wb") as f:
                f.write(raw_data)
                
            logger.debug(f"Saved image to {image_path}")
            
            # Update metadata with file path (relative to parent_dir)
            metadata["file_path"] = str(image_path.relative_to(parent_dir))
            
            # Remove raw data from image data dictionary to save space
            # since we've now saved it to disk
            image.pop("raw_data", None)
            
        except Exception as e:
            logger.warning(f"Failed to save image {index}: {e}")


def process_pdf_for_images(
    pdf_path: Union[str, Path], 
    output_dir: Union[str, Path], 
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a PDF document to extract and save images with proper organization.
    
    This function serves as the main entry point for the image extraction module.
    
    Args:
        pdf_path: Path to the PDF document
        output_dir: Base directory for saving output
        config: Optional configuration dictionary
        
    Returns:
        A dictionary containing extracted images data and metadata
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        RuntimeError: If there's an error during processing
    """
    extractor = EnhancedImageExtractor(config)
    return extractor.extract_and_save_images(pdf_path, output_dir) 