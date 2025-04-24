"""
Docling Integration Module

This module provides helper functions to streamline integration with the docling library,
making it easier to use docling's features for document processing.
"""

# Fix docling imports
import sys
import os
from pathlib import Path

# Add parent directory to sys.path to find docling_fix
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import docling_fix

import logging
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import os

# Debug printing
print ("PYTHONPATH:", os.environ.get("PYTHONPATH"))

# Import docling library components
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.datamodel.document import ConversionResult
    from docling_core.types.doc import DoclingDocument
    
    # Configure logging
    logger = logging.getLogger(__name__)
    logger.info("Successfully imported docling modules")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Error importing docling modules: {e}")
    
    # Create placeholder classes for type hints
    class PdfPipelineOptions:
        """Placeholder for PdfPipelineOptions class"""
        def __init__(self):
            self.images_scale = 2.0
            self.generate_page_images = True
            self.generate_picture_images = True
            self.do_picture_description = True
            self.do_table_structure = True
            self.allow_external_plugins = True
    
    class DoclingDocument:
        """Placeholder for DoclingDocument class"""
        pass

def create_pdf_pipeline_options(
    images_scale: float = 2.0,
    generate_page_images: bool = True,
    generate_picture_images: bool = True,
    do_picture_description: bool = True,
    do_table_structure: bool = True,
    allow_external_plugins: bool = True,
    **additional_options
) -> PdfPipelineOptions:
    """
    Create PDF pipeline options with common settings.
    
    Args:
        images_scale: Scale factor for images (default: 2.0)
        generate_page_images: Whether to generate images for pages (default: True)
        generate_picture_images: Whether to generate images for pictures (default: True)
        do_picture_description: Whether to generate descriptions for pictures (default: True)
        do_table_structure: Whether to extract table structure (default: True)
        allow_external_plugins: Whether to allow external plugins (default: True)
        additional_options: Additional options to set on the pipeline
        
    Returns:
        PdfPipelineOptions: Configured pipeline options
    """
    pipeline_options = PdfPipelineOptions()
    
    # Set basic options
    pipeline_options.images_scale = images_scale
    pipeline_options.generate_page_images = generate_page_images
    pipeline_options.generate_picture_images = generate_picture_images
    pipeline_options.do_picture_description = do_picture_description
    pipeline_options.do_table_structure = do_table_structure
    pipeline_options.allow_external_plugins = allow_external_plugins
    
    # Apply any additional options
    for key, value in additional_options.items():
        if hasattr(pipeline_options, key):
            setattr(pipeline_options, key, value)
        else:
            logger.warning(f"Unknown pipeline option: {key}")
    
    return pipeline_options

def convert_pdf_document(
    pdf_path: Union[str, Path],
    pipeline_options: Optional[PdfPipelineOptions] = None,
    config_file: Optional[Union[str, Path]] = None
) -> DoclingDocument:
    """
    Convert a PDF document to a DoclingDocument using docling.
    
    Args:
        pdf_path: Path to the PDF document
        pipeline_options: Pipeline options for PDF conversion (default: None)
        config_file: Path to configuration file (default: None)
        
    Returns:
        DoclingDocument: The converted document
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        RuntimeError: If the conversion fails
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Use default pipeline options if none provided
    if pipeline_options is None:
        pipeline_options = create_pdf_pipeline_options()
    
    # Apply configuration from file if provided
    if config_file is not None:
        config_path = Path(config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Apply configuration settings to pipeline options
                for key, value in config.get('pdf_pipeline_options', {}).items():
                    if hasattr(pipeline_options, key):
                        setattr(pipeline_options, key, value)
                        logger.debug(f"Applied configuration setting: {key}={value}")
                    else:
                        logger.warning(f"Unknown pipeline option in config: {key}")
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
    
    try:
        # Create a DocumentConverter with the PDF format option
        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        # Convert the PDF document
        logger.info(f"Converting PDF document: {pdf_path}")
        conversion_result = doc_converter.convert(pdf_path)
        
        # Check conversion status
        if conversion_result.status != "success":
            raise RuntimeError(f"PDF conversion failed: {conversion_result.status}")
        
        # Return the DoclingDocument
        logger.info("PDF conversion completed successfully")
        return conversion_result.document
        
    except Exception as e:
        logger.exception(f"Error converting PDF: {e}")
        raise RuntimeError(f"Failed to convert PDF: {e}")

def extract_document_metadata(docling_document: DoclingDocument) -> Dict[str, Any]:
    """
    Extract metadata from a DoclingDocument.
    
    Args:
        docling_document: The DoclingDocument
        
    Returns:
        Dict[str, Any]: Dictionary containing document metadata
    """
    metadata = {
        "name": getattr(docling_document, 'name', 'unknown'),
        "page_count": len(getattr(docling_document, 'pages', [])),
        "has_tables": False,
        "has_pictures": False,
        "has_forms": False,
    }
    
    # Check for tables
    table_count = 0
    for page in getattr(docling_document, 'pages', []):
        table_count += len(getattr(page, 'tables', []))
    
    if table_count > 0:
        metadata["has_tables"] = True
        metadata["table_count"] = table_count
    
    # Check for pictures
    picture_count = 0
    for page in getattr(docling_document, 'pages', []):
        picture_count += len(getattr(page, 'pictures', []))
    
    if picture_count > 0:
        metadata["has_pictures"] = True
        metadata["picture_count"] = picture_count
    
    # Get additional metadata if available
    if hasattr(docling_document, 'metadata'):
        doc_metadata = getattr(docling_document, 'metadata', {})
        # Add document metadata while avoiding overwriting existing keys
        for key, value in doc_metadata.items():
            if key not in metadata:
                metadata[key] = value
    
    return metadata

def serialize_docling_document(docling_document: Union[DoclingDocument, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Serialize a DoclingDocument to a dictionary, handling any exceptions.
    
    Args:
        docling_document: The DoclingDocument or a dictionary representation
        
    Returns:
        Dict[str, Any]: Dictionary representation of the document
        
    Raises:
        TypeError: If the document cannot be serialized
    """
    try:
        # If docling_document is already a dictionary, just return it
        if isinstance(docling_document, dict):
            logger.info("Input is already a dictionary, skipping serialization")
            return docling_document
            
        # Use the document's export_to_dict method if available
        if hasattr(docling_document, 'export_to_dict'):
            return docling_document.export_to_dict()
        
        # Fall back to direct dictionary conversion
        logger.warning("DoclingDocument does not have export_to_dict method, using direct conversion")
        return docling_document.dict()
        
    except Exception as e:
        logger.exception(f"Error serializing DoclingDocument: {e}")
        raise TypeError(f"Failed to serialize DoclingDocument: {e}")

def merge_with_image_data(
    document_dict: Dict[str, Any],
    images_data_path: Union[str, Path]
) -> Dict[str, Any]:
    """
    Merge document dictionary with image data from a JSON file.
    
    Args:
        document_dict: Dictionary representation of the document
        images_data_path: Path to the images_data.json file
        
    Returns:
        Dict[str, Any]: Merged dictionary with image data
    """
    images_data_path = Path(images_data_path)
    if not images_data_path.exists():
        logger.warning(f"Images data file not found: {images_data_path}")
        return document_dict
    
    try:
        with open(images_data_path, 'r', encoding='utf-8') as f:
            images_data = json.load(f)
        
        # Create a copy of the document dictionary
        result = document_dict.copy()
        
        # Add image data to the document dictionary
        result['images_data'] = images_data
        logger.info(f"Successfully merged image data from {images_data_path}")
        
        return result
        
    except Exception as e:
        logger.warning(f"Error merging image data: {e}")
        return document_dict 