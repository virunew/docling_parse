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
            images_data_file = output_dir / "images_data.json"
            if images_data_file.exists():
                logger.debug("Found images_data.json, incorporating image data...")
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
        
        # Extract images from the PDF document using PDFImageExtractor
        logger.info("Extracting images from the PDF document")
        config = {
            'images_scale': 2.0,
            'do_picture_description': True,
            'do_table_structure': True,
            'allow_external_plugins': True
        }
        image_extractor = PDFImageExtractor(config)
        try:
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
            
            # Analyze image relationships with surrounding text
            element_map = build_element_map(docling_document)
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
        
        except Exception as img_err:
            logger.warning(f"Image extraction encountered an error: {img_err}")
            logger.warning("Continuing with document processing without images")
        
        # Return the DoclingDocument directly
        return docling_document
        
    except Exception as e:
        logger.exception(f"Error processing PDF document: {e}")
        raise
