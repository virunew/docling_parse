"""
PDF Parsing Helper Module

This module provides helper functions for processing PDF documents using the docling library.
It includes functions for converting PDF documents, saving output to JSON, and extracting
images with enhanced processing capabilities.
"""

# Fix docling imports
import docling_fix

import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union

# Import docling integration functions
from docling_integration import (
    create_pdf_pipeline_options,
    convert_pdf_document,
    extract_document_metadata,
    serialize_docling_document,
    merge_with_image_data
)

# Import local modules
from element_map_builder import build_element_map
from logger_config import logger
from pdf_image_extractor import ImageContentRelationship, PDFImageExtractor
from image_extraction_module import process_pdf_for_images, EnhancedImageExtractor
from metadata_extractor import extract_full_metadata, build_metadata_object


def save_output(docling_document, output_dir):
    """
    Save a DoclingDocument as a JSON file.
    
    Args:
        docling_document: The DoclingDocument to save
        output_dir: Directory to save output files
        
    Returns:
        Path to the saved JSON file
    """
    try:
        logger.info("Saving output document as JSON")
        
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get the document name
        doc_name = getattr(docling_document, 'name', 'docling_document')
        
        # Serialize the document to a dictionary
        doc_dict = serialize_docling_document(docling_document)
        
        # Check if there's an images_data.json file to incorporate
        doc_dir = output_path / doc_name
        images_data_path = doc_dir / "images_data.json"
        
        if images_data_path.exists():
            logger.info(f"Found images data at {images_data_path}, incorporating into output")
            doc_dict = merge_with_image_data(doc_dict, images_data_path)
        
        # Write the JSON output
        output_file = output_path / f"{doc_name}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(doc_dict, f, indent=2)
        
        logger.info(f"Document saved to {output_file}")
        return output_file
        
    except IOError as e:
        logger.error(f"IO error saving output: {e}")
        raise
    except TypeError as e:
        logger.error(f"Type error in save_output (document serialization failed): {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in save_output: {e}")
        raise


def process_pdf_document(pdf_path, output_dir, config_file=None):
    """
    Process a PDF document and extract its content.
    
    Args:
        pdf_path: Path to the PDF document
        output_dir: Directory to save output files
        config_file: Path to the configuration file (optional)
    
    Returns:
        DoclingDocument: The converted document object
    """
    logger.info(f"Processing PDF document: {pdf_path}")
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Convert the PDF document to a DoclingDocument
        pipeline_options = create_pdf_pipeline_options(
            images_scale=2.0,
            generate_page_images=True,
            generate_picture_images=True,
            do_picture_description=True,
            do_table_structure=True,
            allow_external_plugins=True
        )
        
        logger.info("Converting PDF document...")
        docling_document = convert_pdf_document(
            pdf_path,
            pipeline_options=pipeline_options,
            config_file=config_file
        )
        
        # Get document name for directory structure
        doc_name = getattr(docling_document, 'name', 'docling_document')
        
        # Create file-specific output directory
        file_output_dir = output_path / doc_name
        file_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 2: Build and save the element map
        logger.info("Building element map...")
        element_map = build_element_map(docling_document)
        
        # Save the element map to the file-specific directory
        element_map_path = file_output_dir / "element_map.json"
        with open(element_map_path, 'w', encoding='utf-8') as f:
            json.dump(element_map, f, indent=2)
        logger.info(f"Element map saved to {element_map_path}")
        
        # Step 3: Extract metadata
        logger.info("Extracting document metadata...")
        doc_info = {
            'filename': Path(pdf_path).name,
            'mimetype': 'application/pdf'
        }
        
        # If element map has a flattened sequence, extract metadata for each element
        metadata_processed = 0
        if element_map and 'flattened_sequence' in element_map:
            flattened_sequence = element_map.get('flattened_sequence', [])
            
            # Process metadata for each element in the sequence
            logger.info("Extracting metadata for document elements")
            for i, element in enumerate(flattened_sequence):
                try:
                    # Extract full metadata for the element
                    metadata = extract_full_metadata(element, flattened_sequence, doc_info)
                    
                    # Add metadata to the element
                    element['extracted_metadata'] = metadata
                    metadata_processed += 1
                    
                    # Log progress for large documents
                    if i % 100 == 0 and i > 0:
                        logger.debug(f"Processed metadata for {i} elements")
                        
                except Exception as meta_err:
                    logger.warning(f"Error extracting metadata for element {i}: {meta_err}")
            
            # Save the updated element map with metadata
            metadata_map_path = file_output_dir / "element_map_with_metadata.json"
            with open(metadata_map_path, 'w', encoding='utf-8') as f:
                json.dump(element_map, f, indent=2)
            logger.info(f"Element map with metadata saved to {metadata_map_path} ({metadata_processed} elements processed)")
        
        # Step 4: Extract images from the PDF document
        logger.info("Extracting images from the PDF document...")
        
        # Load config for image extraction from file if available
        image_extraction_config = {
            'images_scale': 2.0,
            'do_picture_description': True,
            'do_table_structure': True,
            'allow_external_plugins': True,
            'max_workers': 4,  # Use 4 parallel workers by default
            'max_retries': 3,  # Retry failed image extractions up to 3 times
            'processing_timeout': 300  # 5 minutes timeout for large documents
        }
        
        # If config_file is provided, try to load image extraction settings
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    
                # Update config with values from file if they exist
                if 'image_extraction' in file_config:
                    for key, value in file_config['image_extraction'].items():
                        image_extraction_config[key] = value
                    logger.info(f"Loaded image extraction configuration from {config_file}")
            except Exception as config_err:
                logger.warning(f"Error loading config file {config_file}: {config_err}")
        
        # Extract images using the enhanced module
        try:
            logger.info("Using enhanced image extraction with parallel processing")
            images_data = process_pdf_for_images(pdf_path, output_path, image_extraction_config)
            
            # Log extraction statistics if available
            if 'extraction_stats' in images_data:
                stats = images_data['extraction_stats']
                logger.info(f"Image extraction completed: {stats.get('successful', 0)} images extracted, "
                          f"{stats.get('failed', 0)} failed, in {stats.get('total_time', 0):.2f} seconds")
            else:
                logger.info(f"Successfully processed images from {pdf_path}")
                
        except Exception as img_err:
            logger.warning(f"Enhanced image extraction encountered an error: {img_err}")
            logger.warning("Falling back to legacy image extraction")
            
            # Fallback to legacy image extraction directly with PDFImageExtractor
            try:
                logger.info("Attempting legacy image extraction as fallback")
                image_extractor = PDFImageExtractor(image_extraction_config)
                images_data = image_extractor.extract_images(pdf_path)
                logger.info(f"Successfully extracted {len(images_data.get('images', []))} images using legacy extractor")
                
                # Create image output directory
                images_dir = file_output_dir / "images"
                images_dir.mkdir(exist_ok=True)
                
                # Process images and save them to disk
                process_extracted_images(images_data, images_dir, file_output_dir)
                
                # Analyze image relationships with surrounding text if element map is available
                if element_map and 'flattened_sequence' in element_map:
                    # Get the flattened sequence and elements dictionary from the element map
                    flattened_sequence = element_map.get("flattened_sequence", [])
                    elements_dict = element_map.get("elements", {})
                    
                    if flattened_sequence:
                        relationship_analyzer = ImageContentRelationship(
                            elements_dict, 
                            flattened_sequence
                        )
                        enhanced_images_data = relationship_analyzer.analyze_relationships(images_data)
                        
                        # Save the enhanced image data as JSON
                        images_json_path = file_output_dir / "images_data.json"
                        with open(images_json_path, "w", encoding="utf-8") as f:
                            json.dump(enhanced_images_data, f, indent=2)
                        logger.info(f"Image extraction data saved to {images_json_path}")
                    else:
                        logger.warning("No flattened sequence found in the element map, skipping relationship analysis")
                else:
                    logger.warning("Failed to build element map for document, skipping relationship analysis")
            except Exception as legacy_img_err:
                logger.warning(f"Legacy image extraction also failed: {legacy_img_err}")
                logger.warning("Continuing with document processing without images")
        
        # Return the DoclingDocument directly
        return docling_document
        
    except Exception as e:
        logger.exception(f"Error processing PDF document: {e}")
        raise


def process_extracted_images(images_data, images_dir, output_path):
    """
    Process extracted images, save them to disk, and update metadata.
    
    Args:
        images_data: The extracted images data dictionary
        images_dir: Directory to save the images
        output_path: Base output path for relative path calculation
    """
    # Save extracted images to disk if they have raw data
    saved_count = 0
    failed_count = 0
    
    for i, image in enumerate(images_data.get("images", [])):
        try:
            if image.get("raw_data"):
                image_id = image.get("metadata", {}).get("id", f"image_{i}")
                image_format = image.get("metadata", {}).get("format", "image/png").split("/")[-1]
                image_path = images_dir / f"{image_id}.{image_format}"
                
                with open(image_path, "wb") as f:
                    f.write(image.get("raw_data"))
                
                # Update the image path in metadata
                image["metadata"]["file_path"] = str(image_path.relative_to(output_path))
                
                # Remove raw_data bytes since data_uri already contains the base64 encoded data
                image.pop("raw_data", None)
                
                saved_count += 1
        except Exception as e:
            logger.warning(f"Error saving image {i}: {e}")
            failed_count += 1
    
    logger.info(f"Processed {saved_count + failed_count} images: {saved_count} saved, {failed_count} failed")
    
    # Save the updated images data with file paths
    try:
        images_json_path = output_path / "images_data.json"
        with open(images_json_path, "w", encoding="utf-8") as f:
            json.dump(images_data, f, indent=2)
        logger.info(f"Basic image data saved to {images_json_path}")
    except Exception as e:
        logger.warning(f"Failed to save images data JSON: {e}")
