#!/usr/bin/env python3
"""
Test script for PDF image extraction using the docling library.

This test script processes a PDF document, extracts images, and verifies
that the image extraction functionality is working correctly.
"""

import os
import sys
import logging
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the modules to be tested
from pdf_image_extractor import PDFImageExtractor, ImageContentRelationship
from element_map_builder import build_element_map
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions

# Set up logging for the test
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_image_extraction(pdf_path, output_dir):
    """
    Test the image extraction functionality.
    
    Args:
        pdf_path: Path to the PDF document
        output_dir: Directory to save extracted images
    """
    logger.info(f"Testing image extraction for PDF: {pdf_path}")
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Configure image extraction
    config = {
        'images_scale': 2.0,
        'do_picture_description': True,
        'do_table_structure': True,
        'allow_external_plugins': True
    }
    
    try:
        # Create a PDF image extractor
        logger.info("Creating PDFImageExtractor instance")
        image_extractor = PDFImageExtractor(config)
        
        # Extract images from the PDF
        logger.info("Extracting images from PDF")
        images_data = image_extractor.extract_images(pdf_path)
        
        # Check if images were found
        num_images = len(images_data.get("images", []))
        logger.info(f"Found {num_images} images in the PDF")
        
        if num_images == 0:
            logger.warning("No images found in the PDF. Extraction may have failed.")
        
        # Save extracted images to disk if they have raw data
        images_dir = output_path / "images"
        images_dir.mkdir(exist_ok=True)
        
        saved_images = 0
        for i, image in enumerate(images_data.get("images", [])):
            if image.get("raw_data"):
                image_id = image.get("metadata", {}).get("id", f"image_{i}")
                image_format = image.get("metadata", {}).get("format", "image/png").split("/")[-1]
                image_path = images_dir / f"{image_id}.{image_format}"
                
                with open(image_path, "wb") as f:
                    f.write(image.get("raw_data"))
                logger.info(f"Saved image to {image_path}")
                
                # Update the image path in metadata
                image["metadata"]["file_path"] = str(image_path.relative_to(output_path))
                saved_images += 1
        
        logger.info(f"Saved {saved_images} images to {images_dir}")
        
        # Save the images data as JSON for inspection
        images_json_path = output_path / "test_images_data.json"
        with open(images_json_path, "w", encoding="utf-8") as f:
            # We need to remove the raw_data field as it can't be serialized
            serializable_data = images_data.copy()
            for image in serializable_data.get("images", []):
                if "raw_data" in image:
                    del image["raw_data"]
            
            json.dump(serializable_data, f, indent=2)
        logger.info(f"Saved image metadata to {images_json_path}")
        
        # Now convert the document to test the element map and flattened sequence
        logger.info("Converting document for element map testing")
        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = 2.0
        pipeline_options.generate_page_images = True
        pipeline_options.generate_picture_images = True
        
        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        conversion_result = doc_converter.convert(Path(pdf_path))
        docling_document = conversion_result.document
        
        # Build the element map
        logger.info("Building element map")
        element_map = build_element_map(docling_document)
        
        # Check if flattened sequence was created
        flattened_sequence = element_map.get("flattened_sequence", [])
        logger.info(f"Element map built: {len(element_map.get('elements', {}))} elements, {len(flattened_sequence)} in sequence")
        
        # If we have both images and an element map, test image relationships
        if num_images > 0 and flattened_sequence:
            logger.info("Testing image content relationships")
            elements_dict = element_map.get("elements", {})
            relationship_analyzer = ImageContentRelationship(elements_dict, flattened_sequence)
            
            enhanced_images_data = relationship_analyzer.analyze_relationships(images_data)
            
            # Save the enhanced image data as JSON
            enhanced_json_path = output_path / "test_enhanced_images.json"
            with open(enhanced_json_path, "w", encoding="utf-8") as f:
                # Remove raw_data for serialization
                for image in enhanced_images_data.get("images", []):
                    if "raw_data" in image:
                        del image["raw_data"]
                
                json.dump(enhanced_images_data, f, indent=2)
            logger.info(f"Enhanced image data saved to {enhanced_json_path}")
        
        # Final verification
        logger.info("Image extraction test completed:")
        logger.info(f"  - PDF document: {pdf_path}")
        logger.info(f"  - Images found: {num_images}")
        logger.info(f"  - Images saved: {saved_images}")
        logger.info(f"  - Elements in map: {len(element_map.get('elements', {}))}")
        logger.info(f"  - Elements in sequence: {len(flattened_sequence)}")
        logger.info(f"  - Image data saved to: {images_json_path}")
        
        # Return the number of images found
        return num_images
        
    except Exception as e:
        logger.exception(f"Error testing image extraction: {e}")
        return 0

def main():
    """Main function to run the test."""
    # Get command line arguments
    if len(sys.argv) < 3:
        print("Usage: python test_image_extraction.py <pdf_path> <output_dir>")
        return 1
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Check if the PDF file exists
    if not os.path.isfile(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return 1
    
    # Run the test
    num_images = test_image_extraction(pdf_path, output_dir)
    
    # Return success if at least one image was found
    return 0 if num_images > 0 else 1

if __name__ == "__main__":
    sys.exit(main()) 