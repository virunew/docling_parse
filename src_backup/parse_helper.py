import logging
import os
import json
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from element_map_builder import build_element_map
from logger_config import logger
from pdf_image_extractor import ImageContentRelationship, PDFImageExtractor
# Import the new enhanced image extraction module
from image_extraction_module import process_pdf_for_images
# Import the metadata extractor module
from metadata_extractor import extract_full_metadata, build_metadata_object


def save_output(docling_document, output_dir):
    """
    Save the DoclingDocument as a JSON file

    Args:
        docling_document (DoclingDocument): The document to save
        output_dir (str or Path): Directory where to save the output

    Returns:
        Path: Path to the saved output file

    Raises:
        IOError: If the output directory is not writable
        TypeError: If the document cannot be exported to dict
        Exception: For other errors
    """
    logger.info(f"Saving DoclingDocument to {output_dir}")

    try:
        output_dir = Path(output_dir)

        # Get the document name for the output filename
        doc_name = getattr(docling_document, 'name', 'docling_document')
        output_file = output_dir / f"{doc_name}.json"

        try:
            # Get a dictionary representation of the document
            logger.debug("Exporting DoclingDocument to dict...")
            doc_dict = docling_document.export_to_dict()

            # Check if images_data.json exists, and if so, include it in the output
            # First check in the file-specific directory
            file_output_dir = output_dir / doc_name
            images_data_file = file_output_dir / "images_data.json"
            
            # If not found in file-specific directory, check in the base output directory
            if not images_data_file.exists():
                images_data_file = output_dir / "images_data.json"
                
            if images_data_file.exists():
                logger.debug(f"Found images_data.json at {images_data_file}, incorporating image data...")
                try:
                    with open(images_data_file, 'r', encoding='utf-8') as f:
                        images_data = json.load(f)

                    # Add image data to the document dictionary
                    doc_dict['images_data'] = images_data
                    logger.info("Successfully added image data to the output")
                except Exception as img_err:
                    logger.warning(f"Error incorporating image data: {img_err}")
                    logger.warning("Continuing without including image data in the output")

            # Write the dictionary to a JSON file
            logger.debug(f"Writing JSON to {output_file}...")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(doc_dict, f, indent=2)

            logger.info(f"DoclingDocument saved successfully to {output_file}")
            return output_file

        except AttributeError as e:
            logger.error(f"Failed to export DoclingDocument: {e}")
            raise TypeError(f"DoclingDocument export_to_dict method failed: {e}")

        except json.JSONDecodeError as e:
            logger.error(f"JSON serialization error: {e}")
            raise Exception(f"Failed to serialize DoclingDocument to JSON: {e}")

    except IOError as e:
        logger.error(f"Failed to write output file: {e}")
        raise IOError(f"Could not write to {output_dir}: {e}")

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
        # Set up pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = 2.0  # Adjust image resolution if needed
        pipeline_options.generate_page_images = True  # Generate images for pages
        pipeline_options.generate_picture_images = True  # Generate images for pictures
        pipeline_options.allow_external_plugins = True
        pipeline_options.do_picture_description = True
        pipeline_options.do_table_structure = True
        
        # Enable external plugins if a config file is provided
        if config_file and Path(config_file).exists():
            pipeline_options.allow_external_plugins = True
            logger.info(f"Using configuration file: {config_file}")
            # Load environment variables for docling configuration
            os.environ["DOCLING_CONFIG_FILE"] = str(Path(config_file).absolute())
        
        # Create a DocumentConverter instance
        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        # Convert the PDF document
        logger.debug(f"Starting document conversion")
        conversion_result = doc_converter.convert(Path(pdf_path))
        
        # Check conversion status
        if conversion_result.status != "success":
            raise Exception(f"Document conversion failed: {conversion_result.status}")
            
        docling_document = conversion_result.document
        logger.info(f"Document successfully converted: {len(docling_document.pages)} pages found")
        
        # Create the element map and save it
        logger.info("Building element map")
        element_map = build_element_map(docling_document)
        doc_name = getattr(docling_document, 'name', 'docling_document')
        
        # Create file-specific output directory
        file_output_dir = output_path / doc_name
        file_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the element map to the file-specific directory
        element_map_path = file_output_dir / "element_map.json"
        with open(element_map_path, 'w', encoding='utf-8') as f:
            json.dump(element_map, f, indent=2)
        logger.info(f"Element map saved to {element_map_path}")
        
        # Get document information for metadata
        doc_info = {
            'filename': Path(pdf_path).name,
            'mimetype': 'application/pdf'
        }
        
        # If element map has a flattened sequence, extract metadata for each element
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
                    
                    # Log progress for large documents
                    if i % 100 == 0 and i > 0:
                        logger.debug(f"Processed metadata for {i} elements")
                        
                except Exception as meta_err:
                    logger.warning(f"Error extracting metadata for element {i}: {meta_err}")
            
            # Save the updated element map with metadata
            metadata_map_path = file_output_dir / "element_map_with_metadata.json"
            with open(metadata_map_path, 'w', encoding='utf-8') as f:
                json.dump(element_map, f, indent=2)
            logger.info(f"Element map with metadata saved to {metadata_map_path}")
        
        # Extract images from the PDF document using the enhanced image extractor
        logger.info("Extracting images from the PDF document")
        config = {
            'images_scale': 2.0,
            'do_picture_description': True,
            'do_table_structure': True,
            'allow_external_plugins': True
        }
        
        try:
            # Use the new enhanced image extraction module
            images_data = process_pdf_for_images(pdf_path, output_path, config)
            logger.info(f"Successfully processed images from {pdf_path}")
        except Exception as img_err:
            logger.warning(f"Enhanced image extraction encountered an error: {img_err}")
            logger.warning("Falling back to legacy image extraction")
            
            # Fallback to legacy image extraction directly with PDFImageExtractor
            try:
                image_extractor = PDFImageExtractor(config)
                images_data = image_extractor.extract_images(pdf_path)
                logger.info(f"Successfully extracted {len(images_data.get('images', []))} images from the PDF")
                
                # Create image output directory
                images_dir = output_path / "images"
                images_dir.mkdir(exist_ok=True)
                
                # Save extracted images to disk if they have raw data
                for i, image in enumerate(images_data.get("images", [])):
                    if image.get("raw_data"):
                        image_id = image.get("metadata", {}).get("id", f"image_{i}")
                        image_format = image.get("metadata", {}).get("format", "image/png").split("/")[-1]
                        image_path = images_dir / f"{image_id}.{image_format}"
                        
                        with open(image_path, "wb") as f:
                            f.write(image.get("raw_data"))
                        logger.debug(f"Saved image to {image_path}")
                        
                        # Update the image path in metadata
                        image["metadata"]["file_path"] = str(image_path.relative_to(output_path))
                        
                        # Convert raw_data bytes to base64 string for JSON serialization
                        # We'll remove raw_data after conversion since data_uri already contains the base64 encoded data
                        image.pop("raw_data", None)
                
                # Analyze image relationships with surrounding text if element map is available
                if element_map:
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
                        images_json_path = output_path / "images_data.json"
                        with open(images_json_path, "w", encoding="utf-8") as f:
                            json.dump(enhanced_images_data, f, indent=2)
                        logger.info(f"Image extraction data saved to {images_json_path}")
                    else:
                        logger.warning("No flattened sequence found in the element map")
                        logger.warning("Image relationship analysis skipped")
                else:
                    logger.warning("Failed to build element map for document")
                    logger.warning("Image relationship analysis skipped")
            except Exception as legacy_img_err:
                logger.warning(f"Legacy image extraction also failed: {legacy_img_err}")
                logger.warning("Continuing with document processing without images")
        
        # Return the DoclingDocument directly
        return docling_document
        
    except Exception as e:
        logger.exception(f"Error processing PDF document: {e}")
        raise
