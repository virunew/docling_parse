#!/usr/bin/env python3
"""
Streamlined Processor for Docling Documents

This module provides a streamlined processing function that takes a docling document
and processes it directly to the final output format without saving intermediate files.
"""

import logging
from pathlib import Path
import json

# Import necessary functions
from src.json_metadata_fixer import fix_metadata
from src.utils import replace_base64_with_file_references
from output_formatter import OutputFormatter
from src.parse_helper import save_output_to_dict


def streamlined_process(docling_document, output_dir, pdf_path, formatter_config, output_format="json"):
    """
    Process document data directly to final output without saving intermediate files.
    
    Args:
        docling_document: Docling document data (DoclingDocument object or dictionary)
        output_dir: Directory to save outputs
        pdf_path: Path to source PDF
        formatter_config: Configuration for formatter
        output_format: Output format type
        
    Returns:
        Path to formatted output file
    """
    logger = logging.getLogger(__name__)
    
    # Convert DoclingDocument to dictionary if necessary
    if hasattr(docling_document, '__class__') and docling_document.__class__.__name__ == 'DoclingDocument':
        logger.info("Converting DoclingDocument object to dictionary")
        document_data = save_output_to_dict(docling_document)
    else:
        # Already a dictionary
        document_data = docling_document
    
    # Apply metadata fixes directly to the document data
    logger.info("Applying metadata fixes to the document")
    fixed_document_data = fix_metadata(document_data, output_dir)
    
    # Determine document ID from PDF path
    doc_id = Path(pdf_path).stem
    
    # Create output directory
    doc_output_dir = Path(output_dir)
    
    # Replace base64 image data with file references
    logger.info(f"Replacing base64 image data with file references")
    fixed_document_data_for_storage = replace_base64_with_file_references(
        fixed_document_data, 
        doc_output_dir,
        doc_id
    )
    
    # Create formatter and save final output
    formatter = OutputFormatter(formatter_config)
    
    # Format the document data first
    try:
        if output_format.lower() == "json":
            formatted_data = formatter.format_as_simplified_json(fixed_document_data_for_storage)
            output_file = doc_output_dir / "document_simplified.json"
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        
        elif output_format.lower() == "md":
            formatted_data = formatter.format_as_markdown(fixed_document_data_for_storage)
            output_file = doc_output_dir / "document.md"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted_data)
                
        elif output_format.lower() == "html":
            formatted_data = formatter.format_as_html(fixed_document_data_for_storage)
            output_file = doc_output_dir / "document.html"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted_data)
                
        elif output_format.lower() == "csv":
            formatted_data = formatter.format_as_csv(fixed_document_data_for_storage)
            output_file = doc_output_dir / "document.csv"
            
            with open(output_file, "w", encoding="utf-8", newline="") as f:
                f.write(formatted_data)
        else:
            # Default to simplified JSON
            formatted_data = formatter.format_as_simplified_json(fixed_document_data_for_storage)
            output_file = doc_output_dir / "document_simplified.json"
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(formatted_data, f, ensure_ascii=False, indent=2)
                
        logger.info(f"Saved formatted output to {output_file}")
        return str(output_file)
    except Exception as e:
        logger.error(f"Error formatting output: {e}")
        # Create a simple error file with information
        error_file = doc_output_dir / "error.json"
        with open(error_file, "w", encoding="utf-8") as f:
            json.dump({"error": str(e)}, f, ensure_ascii=False, indent=2)
        return str(error_file) 