"""
PDF Image Extraction Module

This module extends the functionality of the pdf_image_extractor.py module to 
provide enhanced organization of extracted images. It ensures that images are saved
in a directory structure that matches the original file names and provides 
additional utilities for image processing.

The module supports parallel processing for better performance when handling 
PDFs with many images, with retry functionality for handling transient errors.
"""

import logging
import os
import json
import time
import traceback
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
import random

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

# Import common utilities
from src.utils import remove_base64_data

# Configure logging
logger = logging.getLogger(__name__)


def retry_operation(
    operation: Callable,
    args: tuple = (),
    kwargs: dict = None,
    max_retries: int = 3,
    base_delay: float = 0.5,
    jitter: float = 0.25,
    max_delay: float = 5.0
) -> Any:
    """
    Retry an operation with exponential backoff and jitter.
    
    Args:
        operation: The function to retry
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        jitter: Random jitter to add to delay (in seconds)
        max_delay: Maximum delay between retries (in seconds)
        
    Returns:
        The result of the operation, if successful
        
    Raises:
        The last exception encountered if all retries fail
    """
    kwargs = kwargs or {}
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                logger.debug(f"Retry attempt {attempt}/{max_retries}")
            return operation(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if attempt < max_retries:
                retry_delay = min(base_delay * (2 ** attempt) + random.uniform(0, jitter), max_delay)
                logger.debug(f"Operation failed: {e}. Retrying in {retry_delay:.2f}s")
                time.sleep(retry_delay)
            else:
                logger.warning(f"All {max_retries} retry attempts failed with: {e}")
    
    # If we get here, all retries failed
    if last_exception:
        raise last_exception
    
    # This should never happen, but just in case
    raise RuntimeError("Retry operation failed but no exception was captured")


class EnhancedImageExtractor:
    """
    Enhanced PDF image extractor that organizes extracted images by file name.
    
    This class builds upon the PDFImageExtractor functionality to ensure that
    extracted images are saved in a directory structure that matches the original
    file names, improving organization and traceability.
    
    It also adds support for parallel processing to improve performance when
    handling PDFs with many images.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced PDF image extractor.
        
        Args:
            config: Optional configuration dictionary with extraction settings
        """
        self.config = config or {}
        self.image_extractor = PDFImageExtractor(self.config)
        
        # Default to 4 workers, but allow configuration
        self.max_workers = self.config.get('max_workers', 4)
        
        # Default processing timeout (seconds)
        self.timeout = self.config.get('processing_timeout', 120)
        
        # Retry settings
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)
        self.backoff_factor = self.config.get('backoff_factor', 2.0)
        
        # Track successful and failed image extractions
        self.extraction_stats = {
            'successful': 0,
            'failed': 0,
            'retried': 0,
            'total_time': 0
        }
        
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
        
        start_time = time.time()
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        logger.info(f"Extracting images from PDF: {pdf_path}")
        
        try:
            # Extract images using the base extractor with retry
            try:
                images_data = retry_operation(
                    self.image_extractor.extract_images,
                    args=(pdf_path,),
                    max_retries=self.max_retries,
                    base_delay=self.retry_delay,
                    jitter=self.retry_delay,
                    max_delay=self.timeout
                )
            except Exception as e:
                logger.warning(f"Image extraction failed after retries: {e}")
                # Create a minimal structure to continue processing
                images_data = {
                    "images": [],
                    "metadata": {
                        "file_path": str(pdf_path),
                        "extraction_error": str(e)
                    }
                }
            
            # Create file-specific output directory using the file's stem (name without extension)
            file_output_dir = output_dir / pdf_path.stem
            file_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create images directory within the file-specific directory
            images_dir = file_output_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            logger.info(f"Saving extracted images to {images_dir}")
            
            # Get the images to process
            images = images_data.get("images", [])
            
            # Log the number of images found
            logger.info(f"Found {len(images)} images in PDF document")
            
            # Process and save images in parallel if there are multiple images
            if len(images) > 1 and self.max_workers > 1:
                self._process_images_parallel(images, images_dir, file_output_dir)
            else:
                # Process images sequentially for small number of images
                for i, image in enumerate(images):
                    try:
                        self._save_image_with_retry(image, i, images_dir, file_output_dir)
                        self.extraction_stats['successful'] += 1
                    except Exception as e:
                        self.extraction_stats['failed'] += 1
                        logger.warning(f"Failed to save image {i} after retries: {e}")
                
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
                    logger.debug(f"Relationship analysis error details: {traceback.format_exc()}")
            else:
                logger.info("No element map found. Skipping relationship analysis.")
                
                # Save the basic images data
                images_data_path = file_output_dir / "images_data.json"
                with open(images_data_path, 'w', encoding='utf-8') as f:
                    json.dump(images_data, f, indent=2)
                    
                logger.info(f"Basic image data saved to {images_data_path}")
            
            # Record extraction stats
            self.extraction_stats['total_time'] = time.time() - start_time
            images_data['extraction_stats'] = self.extraction_stats
            
            logger.info(f"Image extraction completed: {self.extraction_stats['successful']} successful, "
                       f"{self.extraction_stats['failed']} failed, "
                       f"{self.extraction_stats['retried']} retried, "
                       f"in {self.extraction_stats['total_time']:.2f} seconds")
            
            # Create a copy with base64 data removed to reduce file size
            result_for_storage = remove_base64_data(images_data)
            
            # Save the extraction data as JSON
            try:
                json_path = images_data_path
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result_for_storage, f, indent=2)
                logger.info(f"Saved images extraction data to {json_path}")
            except Exception as e:
                logger.warning(f"Failed to save images data JSON: {e}")
            
            return images_data
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.exception(f"Error extracting or saving images after {total_time:.2f} seconds: {e}")
            raise RuntimeError(f"Failed to extract or save images: {e}")
    
    def _process_images_parallel(
        self, 
        images: List[Dict[str, Any]], 
        images_dir: Path, 
        parent_dir: Path
    ) -> None:
        """
        Process and save images in parallel using a thread pool.
        
        Args:
            images: List of image dictionaries to process
            images_dir: Directory to save the images
            parent_dir: Parent directory (for relative path calculation)
        """
        logger.info(f"Processing {len(images)} images in parallel with {self.max_workers} workers")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all image processing tasks to the executor
            future_to_image = {
                executor.submit(
                    self._save_image_with_retry, 
                    image, i, images_dir, parent_dir
                ): (i, image)
                for i, image in enumerate(images)
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_image, timeout=self.timeout):
                idx, _ = future_to_image[future]
                try:
                    future.result()  # Get the result or exception
                    self.extraction_stats['successful'] += 1
                    
                    # Log progress periodically
                    if self.extraction_stats['successful'] % 10 == 0:
                        logger.debug(f"Processed {self.extraction_stats['successful']} images so far")
                        
                except Exception as e:
                    self.extraction_stats['failed'] += 1
                    logger.warning(f"Failed to process image {idx} after retries: {e}")
    
    def _save_image_with_retry(
        self, 
        image: Dict[str, Any], 
        index: int, 
        images_dir: Path, 
        parent_dir: Path
    ) -> None:
        """
        Save an image with retry logic for transient errors.
        
        Args:
            image: Dictionary containing image data and metadata
            index: Index of the image
            images_dir: Directory to save the image
            parent_dir: Parent directory (for relative path calculation)
        """
        try:
            retry_operation(
                self._save_image,
                args=(image, index, images_dir, parent_dir),
                max_retries=self.max_retries,
                base_delay=self.retry_delay,
                jitter=self.retry_delay,
                max_delay=self.timeout
            )
        except Exception as e:
            # If we get here, all retries failed
            self.extraction_stats['failed'] += 1
            # Re-raise to let the parallel processor handle it
            raise RuntimeError(f"Failed to save image {index} after {self.max_retries} retries: {e}")
    
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
        # Get image data and metadata
        raw_data = image.get("raw_data")
        if not raw_data:
            logger.warning(f"No raw data found for image {index}")
            raise ValueError(f"Image {index} has no raw data")
            
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